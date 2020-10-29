from sanic import Sanic
from sanic.response import json
import os
import os.path
from counter import db
from functools import wraps
import json as json_lib

uid = 1


def require_counter():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, cid, *args, **kwargs):
            counter = await db.get_counter(cid, ['count', 'id'])
            if not counter:
                return json({'err': 'counter {} not found.'.format(cid)}, 404)
            return await f(request, counter, cid, *args, **kwargs)

        return decorated_function

    return decorator


def main():
    app = Sanic()

    @app.get('/api/counters/')
    async def get_counters(request):
        offset = int(request.args.get('offset', '0'))
        size = int(request.args.get('size', '10'))
        counters = await db.get_counters(uid, offset, size)
        total = await db.count_counter(uid)

        return json({
            'counters': counters,
            'offset': offset,
            'size': size,
            'total': total
        })

    @app.post('/api/counters/')
    async def create_counter(request):
        name = request.form.get('name')
        remark = request.form.get('remark', '')
        if not name:
            return json({'err': 'name is required'}, '400')
        cid = await db.create_counter(uid, name, remark)
        counter = await db.get_counter(cid)

        return json({'counter': counter})

    @app.get('/api/counters/<cid>/')
    @require_counter()
    async def get_counter(request, counter, cid):
        counter = await db.get_counter(cid)
        return json({'counter': counter})

    @app.post('/api/counters/<cid>/')
    @require_counter()
    async def update_counter(request, counter, cid):
        updated = {}
        for key in ['name', 'remark', 'extra']:
            val = request.form.get(key)
            if val is not None:
                if key == 'extra':
                    try:
                        val = json_lib.loads(val)
                        updated[key] = val
                    except Exception:
                        pass
                else:
                    updated[key] = val

        await db.update_counter(cid, **updated)

        counter = await db.get_counter(cid)
        return json({'counter': counter})

    @app.delete('/api/counters/<cid>/')
    async def remove_counter(request, cid):
        await db.remove_counter(cid)
        return json({'result': 'OK'})

    @app.post('/api/counters/<cid>/histories/')
    @require_counter()
    async def incr_counter(request, counter, cid):
        step = int(request.form.get('step', '0'))
        reason = request.form.get('reason', '')
        await db.incr_counter(cid, step, reason)

        return json({'count': counter['count'] + step})

    @app.get('/api/counters/<cid>/histories/')
    @require_counter()
    async def get_counter_histories(request, counter, cid):
        offset = int(request.args.get('offset', '0'))
        size = int(request.args.get('size', '10'))
        histories = await db.get_counter_histories(cid, offset, size)
        total = await db.count_counter_history(cid)

        return json({
            'histories': histories,
            'offset': offset,
            'size': size,
            'total': total
        })

    @app.listener('after_server_start')
    def init(sanic, loop):
        loop.run_until_complete(db.connect(loop))

    app.run(host='0.0.0.0', port=8080)
