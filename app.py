from sanic import Sanic
from sanic.response import json
import os
import os.path
from counter import db
from functools import wraps
import json as json_lib
import logging

logger = logging.getLogger(__name__)


def get_token(request):
    token = request.headers.get('X-REQUEST-TOKEN')

    if not token:
        if request.method.upper() == 'GET':
            token = request.args.get('token')
        else:
            token = request.form.get('token')
            if not token:
                token = request.args.get('token')

    if not token:
        token = request.cookies.get('token')

    return token


async def current_user(request):
    token = get_token(request)
    if not token:
        return None

    return await get_user_by_token(token)


async def get_user_by_token(token):
    name = await db.get_name(token)
    if not name:
        return None

    return await db.get_user(name=name, columns=['id', 'name'])


def require_login():
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            # run some method that checks the request
            # for the client's authorization status

            u = await current_user(request)
            if u:
                return await f(request, *args, user=u, **kwargs)
            else:
                return json({'err': 'Unauthorized'}, 403)

        return decorated_function

    return decorator


def require_counter(owner=False):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request,
                                     *args,
                                     cid=None,
                                     user=None,
                                     **kwargs):
            counter = await db.get_counter(cid, ['count', 'id', 'uid'])
            if not counter:
                return json({'err': 'counter {} not found.'.format(cid)}, 404)

            if owner:
                if not user:
                    return json({'err': 'No Permession'}, 404)

                if counter['uid'] != user['id']:
                    return json({'err': 'No Permession'}, 404)

            return await f(request,
                           *args,
                           counter=counter,
                           cid=cid,
                           user=user,
                           **kwargs)

        return decorated_function

    return decorator


def main():
    app = Sanic()

    @app.get('/api/counters/')
    @require_login()
    async def get_counters(request, user):
        offset = int(request.args.get('offset', '0'))
        size = int(request.args.get('size', '10'))
        counters = await db.get_counters(user['id'], offset, size)
        total = await db.count_counter(user['id'])

        return json({
            'counters': counters,
            'offset': offset,
            'size': size,
            'total': total
        })

    @app.post('/api/counters/')
    @require_login()
    async def create_counter(request, user):
        name = request.form.get('name')
        remark = request.form.get('remark', '')
        if not name:
            return json({'err': 'name is required'}, '400')
        cid = await db.create_counter(user['id'], name, remark)
        counter = await db.get_counter(cid)

        return json({'counter': counter})

    @app.get('/api/counters/<cid>/')
    @require_login()
    @require_counter(True)
    async def get_counter(request, counter, cid, user):
        counter = await db.get_counter(cid)
        return json({'counter': counter})

    @app.post('/api/counters/<cid>/')
    @require_login()
    @require_counter(True)
    async def update_counter(request, counter, cid, user):
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
    @require_login()
    async def remove_counter(request, cid, user):
        await db.remove_counter(cid)
        return json({'result': 'OK'})

    @app.post('/api/counters/<cid>/histories/')
    @require_login()
    @require_counter(True)
    async def incr_counter(request, counter, cid, user):
        step = int(request.form.get('step', '0'))
        reason = request.form.get('reason', '')
        await db.incr_counter(cid, step, reason)

        return json({'count': counter['count'] + step})

    @app.get('/api/counters/<cid>/histories/')
    @require_login()
    @require_counter(True)
    async def get_counter_histories(request, counter, cid, user):
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

    @app.post('/api/signin')
    async def signin(request):
        name = request.form.get('name')
        password = request.form.get('password')

        if not name:
            return json({'err': 'name is required'}, 400)

        if not password:
            return json({'err': 'password is required'}, 400)

        user = await db.get_user(name=name, columns=['id', 'name', 'password'])

        if not user:
            return json({'err': 'user name or password not correct'}, 403)

        if not db.verify_password(user, password):
            return json({'err': 'user name or password not correct'}, 403)

        token = await db.create_token(name)

        user.pop('password', None)

        return json({'token': token, 'user': user})

    @app.get('/api/users/me')
    @require_login()
    def get_user(request, user):
        return json({'user': user})

    @app.listener('after_server_start')
    def init(sanic, loop):
        loop.run_until_complete(db.connect(loop))

    app.run(host='0.0.0.0', port=8080)
