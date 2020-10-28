from config import pg
from . import pg_utils
from .pg_utils import t, c, i, cs, cs_all, PGConnnector
from time import time
import json

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
                                 offset=offset,
                                 size=size,
                                 other_sql='order by id desc')


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
                                 offset=offset,
                                 size=size,
                                 other_sql='order by id desc')
