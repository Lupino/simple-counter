from functools import wraps
from psycopg2.extras import DictCursor


class TableName(object):
    def __init__(self, table_name, alias=None):
        self.table_name = table_name
        self.alias = alias

    def __str__(self):
        return self.table_name


def get_table_name(table_name):
    if table_name.alias is None:
        return '"{}"'.format(table_name.table_name)
    return '"{}" AS {}'.format(table_name.table_name, table_name.alias)


def t(table_name):
    return TableName(table_name)


class Column(object):
    def __init__(self, column):
        self.column = column

    def __str__(self):
        return self.column


def c(column):
    return Column(column)

c_all = c('*')


def cs(columns):
    return [c(x) for x in columns]

cs_all = cs(['*'])


def columns_to_string(columns):
    return ', '.join([x.column for x in columns])


class IndexName(object):
    def __init__(self, index_name):
        self.index_name = index_name

    def __str__(self):
        return self.index_name


def i(index_name):
    return IndexName(index_name)


def get_index_name(table_name, index_name):
    return '"{}_{}"'.format(table_name.table_name, index_name.index_name)


def constraint_primary_key(table_name, columns):
    return Column('CONSTRAINT {} PRIMARY KEY ({})'.format(
        get_index_name(table_name, i('pk')), columns_to_string(columns)))


class PGConnnector(object):
    def get(self):
        return None

    async def connect(self):
        return True


def run_with_pool(cursor_factory=None):
    def decorator(f):
        @wraps(f)
        async def run(pool, *args, **kwargs):
            try:
                async with pool.get().acquire() as conn:
                    async with conn.cursor(
                            cursor_factory=cursor_factory) as cur:
                        return await f(cur, *args, **kwargs)
            except RuntimeError as e:
                err = str(e)
                if err.find('closing') > -1:
                    connected = await pool.connect()
                    if connected:
                        return await run(pool, *args, **kwargs)
                    else:
                        raise e
                else:
                    raise e

        return run

    return decorator


@run_with_pool()
async def create_table(cur, table_name, columns):
    await cur.execute('CREATE TABLE IF NOT EXISTS {} ({})'.format(
        get_table_name(table_name), columns_to_string(columns)))


@run_with_pool()
async def add_table_column(cur, table_name, columns):
    await cur.execute('ALTER TABLE {} ADD COLUMN {}'.format(
        get_table_name(table_name), columns_to_string(columns)))


@run_with_pool()
async def create_index(cur, uniq, table_name, index_name, columns):
    uniq_word = 'UNIQUE ' if uniq else ''
    await cur.execute('CREATE {}INDEX IF NOT EXISTS {} ON {} ({})'.format(
        uniq_word, get_index_name(table_name, index_name),
        get_table_name(table_name), columns_to_string(columns)))


async def get_only_default(cur, default):
    ret = await cur.fetchone()
    if ret is None:
        return default
    return ret[0]


@run_with_pool()
async def insert(cur,
                 table_name,
                 columns,
                 args,
                 ret_column=None,
                 ret_def=None):
    v = [Column('%s') for x in columns]
    ret_sql = ' returning {}'.format(ret_column.column) if ret_column else ''
    await cur.execute(
        'INSERT INTO {} ({}) VALUES ({}){}'.format(get_table_name(table_name),
                                                   columns_to_string(columns),
                                                   columns_to_string(v),
                                                   ret_sql), args)

    if ret_column:
        return await get_only_default(cur, ret_def)


def append_excluded_set(column):
    col = column.column
    if col.find('=') > -1:
        return col
    return "{} = excluded.{}".format(col, col)


@run_with_pool()
async def insert_or_update(cur,
                           table_name,
                           uniq_columns,
                           value_columns=[],
                           other_columns=[],
                           args=()):
    cols = uniq_columns + value_columns + other_columns
    v = [Column('%s') for x in cols]
    set_sql = ', '.join([append_excluded_set(x) for x in value_columns])
    do_sql = " DO UPDATE SET {}".format(
        set_sql) if value_columns else " DO NOTHING"
    sql = "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) {}".format(
        get_table_name(table_name), columns_to_string(cols),
        columns_to_string(v), columns_to_string(uniq_columns), do_sql)

    await cur.execute(sql, args)


def append_update_set(column):
    col = column.column
    if col.find('=') > -1:
        return col
    return "{} = %s".format(col, col)


@run_with_pool()
async def update(cur, table_name, columns, part_sql="", args=()):
    set_sql = ', '.join([append_update_set(x) for x in columns])
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    sql = "UPDATE {} SET {}{}".format(get_table_name(table_name), set_sql,
                                      where_sql)
    await cur.execute(sql, args)


@run_with_pool()
async def delete(cur, table_name, part_sql="", args=()):
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    sql = 'DELETE FROM {}{}'.format(get_table_name(table_name), where_sql)
    await cur.execute(sql, args)


@run_with_pool()
async def sum(cur,
              table_name,
              part_sql="",
              args=(),
              distinct='*',
              join_sql=''):
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    join_sql = ' {} '.format(join_sql) if join_sql else ''
    sql = 'SELECT sum({}) FROM {}{}{}'.format(distinct,
                                              get_table_name(table_name),
                                              join_sql, where_sql)
    await cur.execute(sql, args)
    return await get_only_default(cur, 0)


@run_with_pool()
async def count(cur,
                table_name,
                part_sql="",
                args=(),
                distinct='*',
                join_sql=''):
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    join_sql = ' {} '.format(join_sql) if join_sql else ''
    sql = 'SELECT count({}) FROM {}{}{}'.format(distinct,
                                                get_table_name(table_name),
                                                join_sql, where_sql)
    await cur.execute(sql, args)
    return await get_only_default(cur, 0)


@run_with_pool(cursor_factory=DictCursor)
async def select(cur,
                 table_name,
                 columns,
                 part_sql='',
                 args=(),
                 offset=None,
                 size=None,
                 other_sql="",
                 join_sql=''):
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    join_sql = ' {} '.format(join_sql) if join_sql else ''
    limit_sql = '' if size is None else ' LIMIT {}'.format(size)
    offset_sql = '' if offset is None else ' OFFSET {}'.format(offset)
    sql = "SELECT {} FROM {}{}{} {}{}{}".format(columns_to_string(columns),
                                                get_table_name(table_name),
                                                join_sql, where_sql, other_sql,
                                                limit_sql, offset_sql)
    await cur.execute(sql, args)
    ret = await cur.fetchall()
    return [dict(x) for x in ret]


async def select_only(pool,
                      table_name,
                      column,
                      part_sql='',
                      args=(),
                      offset=None,
                      size=None,
                      other_sql='',
                      join_sql=''):
    ret = await select(pool, table_name, [column], part_sql, args, offset,
                       size, other_sql, join_sql)
    return [x[column.column] for x in ret]


@run_with_pool(cursor_factory=DictCursor)
async def select_one(cur,
                     table_name,
                     columns,
                     part_sql='',
                     args=(),
                     join_sql=''):
    where_sql = ' WHERE {}'.format(part_sql) if part_sql else ''
    join_sql = ' {} '.format(join_sql) if join_sql else ''
    sql = "SELECT {} FROM {}{}{}".format(columns_to_string(columns),
                                         get_table_name(table_name), join_sql,
                                         where_sql)
    await cur.execute(sql, args)
    ret = await cur.fetchone()
    if ret:
        return dict(ret)
    return None


async def select_one_only(pool,
                          table_name,
                          column,
                          part_sql='',
                          args=(),
                          join_sql=''):
    ret = await select_one(pool, table_name, [column], part_sql, args,
                           join_sql)
    if ret:
        return ret[column.column]

    return None


@run_with_pool()
async def drop_table(cur, table_name):
    await cur.execute('drop table {}'.format(get_table_name(table_name)))


def gen_ordering_sql(column, arr):
    ret = []
    for ordering, a in enumerate(arr):
        ret.append('({}, {})'.format(a, ordering))

    return 'JOIN (VALUES {}) AS x (id, ordering) ON {} = x.id'.format(
        ', '.join(ret), column.column), 'ORDER BY x.ordering'
