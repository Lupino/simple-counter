from config import pg
from . import pg_utils
from .pg_utils import t, c, i, PGConnnector

_pg_pool = None

async def connect(loop=None):
    global _pg_pool
    _pg_pool = PGConnnector(loop=loop, config=pg)

    if await _pg_pool.connect():
        await create_table()

    return _pg_pool


async def close():
    pool = _pg_pool.get()
    pool.close()
    await pool.wait_closed()


counter = t('counters') # 计数器
counter_history = t('counter_histories') # 计数器历史记录


async def create_table():
    await pg_utils.create_table(_pg_pool, counter, [
        c("id SERIAL PRIMARY KEY"),
        c("uid INT NOT NULL"),                    # 用户 ID
        c("name VARCHAR(128) NOT NULL"),          # 计数器名字
        c("desc VARCHAR(1500) DEFAULT ''"),       # 计数器描述信息
        c("count INT DEFAULT 0"),                 # 当前计数
        c("extra JSON"),                           # 当前计数
        c('created_at INT NOT NULL'),             # 计数器添加时间
    ])

    await pg_utils.create_index(_pg_pool, False, counters, i('uid'),
                                 [c('uid')])

    await pg_utils.create_table(_pg_pool, counter_history, [
        c("id SERIAL PRIMARY KEY"),
        c("cid INT NOT NULL"),                    # 计数器ID
        c("count INT DEFAULT 0"),                 # 添加或减少个数
        c('created_at INT NOT NULL'),             # 计数器添加时间
    ])

    await pg_utils.create_index(_pg_pool, False, counter_history, i('cid'),
                                 [c('cid')])
