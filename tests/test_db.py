from counter import db

use_db = True


def check_equal(a, b, key=None):
    if key is None:
        if a != b:
            raise Exception("Value must Equal. except: {} but got {}".format(
                a, b))
    else:
        if a[key] != b[key]:
            raise Exception("Value must Equal. except: {} but got {}".format(
                a[key], b[key]))


def check_big(a, b, key=None):
    if key is None:
        if a <= b:
            raise Exception("Value {} > {}".format(a, b))

    else:
        if a[key] <= b[key]:
            raise Exception("Value {} > {}".format(a[key], b[key]))


async def main():
    uid = 1
    name = '测试计数器'
    remark = '这是个小测试'
    cid = await db.create_counter(uid, name, remark)
    check_big(cid, 0)

    counter = await db.get_counter(cid)
    check_equal(counter['id'], cid)
    check_equal(counter['name'], name)
    check_equal(counter['remark'], remark)
    check_equal(counter['count'], 0)

    await db.incr_counter(cid, 1, 'abcd')
    counter = await db.get_counter(cid)
    check_equal(counter['count'], 1)
    await db.incr_counter(cid, 10, 'def')
    counter = await db.get_counter(cid)
    check_equal(counter['count'], 11)
    await db.incr_counter(cid, -3, 'defg')
    counter = await db.get_counter(cid)
    check_equal(counter['count'], 8)

    hists = await db.get_counter_histories(cid)
    total = await db.count_counter_history(cid)
    check_equal(len(hists), total)

    await db.update_counter(cid, name='new name')
    counter = await db.get_counter(cid)
    check_equal(counter['name'], 'new name')
    await db.update_counter(cid, name='new name1', extra={'test': 'test'})
    counter = await db.get_counter(cid)
    check_equal(counter['name'], 'new name1')
    check_equal(counter['extra']['test'], 'test')
    await db.update_counter(cid, name='new name2', extra={'test1': 'test1'})
    counter = await db.get_counter(cid)
    check_equal(counter['name'], 'new name2')
    check_equal(counter['extra']['test'], 'test')
    check_equal(counter['extra']['test1'], 'test1')
    await db.update_counter(cid, extra={'test': 'test2'})
    counter = await db.get_counter(cid)
    check_equal(counter['extra']['test'], 'test2')

    counters = await db.get_counters(uid)
    check_big(len(counters), 0)

    total = await db.count_counter(uid)
    check_equal(len(counters), total)

    for counter in counters:
        await db.remove_counter(counter['id'])
