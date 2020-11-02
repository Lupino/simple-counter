from config import pg
from . import pg_utils
from .pg_utils import t, c, i, cs, cs_all, PGConnnector
from time import time
import json
import hashlib
from uuid import uuid4

_pool = None


async def connect(loop=None):
    global _pool
    _pool = PGConnnector(loop=loop, config=pg)

    if await _pool.connect():
        await create_table()

    return _pool


async def close():
    pool = _pool.get()
    pool.close()
    await pool.wait_closed()


counter = t('counters')  # 计数器
counter_history = t('counter_histories')  # 计数器历史记录

user = t('users')  # 用户表
token = t('tokens')  # 用户登陆 TOKEN 表


async def create_table():
    await pg_utils.create_table(
        _pool,
        counter,
        [
            c("id SERIAL PRIMARY KEY"),
            c("uid INT NOT NULL"),  # 用户 ID
            c("name VARCHAR(128) NOT NULL"),  # 计数器名字
            c("remark VARCHAR(1500) DEFAULT ''"),  # 计数器描述信息
            c("count INT DEFAULT 0"),  # 当前计数
            c("extra JSON"),  # 计数器额外信息
            c('created_at INT NOT NULL'),  # 计数器添加时间
        ])

    await pg_utils.create_index(_pool, False, counter, i('uid'), [c('uid')])

    await pg_utils.create_table(
        _pool,
        counter_history,
        [
            c("id SERIAL PRIMARY KEY"),
            c("cid INT NOT NULL"),  # 计数器ID
            c("count INT DEFAULT 0"),  # 添加或减少个数
            c("reason VARCHAR(150) DEFAULT ''"),  # 计数器描述信息
            c('created_at INT NOT NULL'),  # 计数器添加时间
        ])

    await pg_utils.create_index(_pool, False, counter_history, i('cid'),
                                [c('cid')])

    await pg_utils.create_table(
        _pool,
        user,
        [
            c("id SERIAL PRIMARY KEY"),
            c("name VARCHAR(128) NOT NULL"),  # 用户名
            c("password VARCHAR(128) NOT NULL"),  # 密码
            c("profile JSON"),  # 用户信息
            c('created_at INT NOT NULL'),  # 用户添加时间
        ])

    await pg_utils.create_index(_pool, True, user, i('name'), [c('name')])

    await pg_utils.create_table(_pool, token, [
        c("token VARCHAR(128) NOT NULL"),
        c("name VARCHAR(128) NOT NULL"),
        c("expire_in INT NOT NULL"),
        c('created_at INT NOT NULL'),
    ])

    await pg_utils.create_index(_pool, True, token, i('token'), [c('token')])


async def create_counter_history(cid, count, reason='', cur=None):
    now = int(time())
    await pg_utils.insert(_pool,
                          counter_history,
                          cs(['cid', 'count', 'reason', 'created_at']),
                          (cid, count, reason, now),
                          cur=cur)


async def remove_counter_histories(cid):
    return await pg_utils.delete(_pool, counter_history, 'cid=%s', (cid, ))


async def get_counter_histories(cid, offset=0, size=100, columns=cs_all):
    return await pg_utils.select(_pool,
                                 counter_history,
                                 columns,
                                 'cid=%s', (cid, ),
                                 offset=offset,
                                 size=size,
                                 other_sql='order by id desc')


async def count_counter_history(cid):
    return await pg_utils.count(_pool, counter_history, "cid=%s", (cid, ))


async def create_counter(uid, name, remark):
    now = int(time())
    return await pg_utils.insert(
        _pool, counter,
        cs(['uid', 'name', 'remark', 'count', 'extra', 'created_at']),
        (uid, name, remark, 0, '{}', now), c('id'))


async def update_counter(cid, **kwargs):
    updated = {}
    for key in ['name', 'remark', 'extra']:
        if kwargs.get(key) is not None:
            if key == 'extra':
                old = await get_counter(cid, columns=cs(['extra']))
                ov = old['extra']
                if not ov:
                    ov = {}

                ov.update(kwargs[key])
                updated[key] = json.dumps(ov)
            else:
                updated[key] = kwargs[key]

    columns = list(updated.keys())
    args = list(updated.values())
    args.append(cid)

    await pg_utils.update(_pool, counter, cs(columns), 'id=%s', tuple(args))


async def incr_counter(cid, count, reason=''):
    async def run(cur):
        if count > 0:
            column = 'count = count + {}'.format(count)
        else:
            column = 'count = count - {}'.format(-count)

        await pg_utils.update(_pool,
                              counter,
                              cs([column]),
                              'id=%s', (cid, ),
                              cur=cur)
        await create_counter_history(cid, count, reason, cur=cur)

    await pg_utils.transaction(_pool, run)


async def get_counter(cid, columns=cs_all):
    return await pg_utils.select_one(_pool, counter, columns, 'id=%s', (cid, ))


async def remove_counter(cid):
    await pg_utils.delete(_pool, counter, 'id=%s', (cid, ))
    await remove_counter_histories(cid)


async def get_counters(uid, offset=0, size=100, columns=cs_all):
    return await pg_utils.select(_pool,
                                 counter,
                                 columns,
                                 'uid=%s',
                                 (uid, ),
                                 offset=offset,
                                 size=size,
                                 other_sql='order by id desc')


async def count_counter(uid):
    return await pg_utils.count(_pool, counter, 'uid=%s', (uid, ))


def hash_password(password):
    h = hashlib.sha256()
    h.update(bytes(password, 'utf-8'))
    return h.hexdigest().lower()


async def create_user(name, password):
    now = int(time())
    return await pg_utils.insert(
        _pool, user, cs(['name', 'password', 'profile', 'created_at']),
        (name, hash_password(password), '{}', now), c('id'))


async def get_user(id=None, name=None, columns=cs_all):
    args = ()
    part_sql = ''
    if id is not None:
        args = (id, )
        part_sql = 'id=%s'
    if name is not None:
        args = (name, )
        part_sql = 'name=%s'

    if not part_sql:
        raise Exception('id or name is required')
    return await pg_utils.select_one(_pool, user, columns, part_sql, args)


def verify_password(user, password):
    return user['password'] == hash_password(password)


async def create_token(name, expire_in=86400):
    token_ = uuid4().hex
    now = int(time())
    return await pg_utils.insert(
        _pool, token, cs(['token', 'name', 'expire_in', 'created_at']),
        (token_, name, expire_in, now), c('token'))


async def get_name(token_):
    return await pg_utils.select_one_only(_pool, token, c('name'), 'token=%s',
                                          (token_, ))


async def purge_tokens():
    now = int(time())
    await pg_utils.delete(_pool, token, 'expire_in + created_at < %s', (now, ))
