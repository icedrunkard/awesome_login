# coding=utf-8
import json
from aiohttp import web
from .mail163 import Mail163


async def login(request):
    try:
        obj=await request.json()
    except:
        text = await request.text()
        try:
            obj = json.loads(text)
        except:
            obj = None
    print(obj)
    if isinstance(obj,dict) and obj.get('username') and obj.get('password'):
        username = obj.get('username')
        password = obj.get('password')
        proxies = obj.get('proxies')
        print(username, password, proxies)
        try:
            res = await Mail163.res_from_instance(username,password,proxies=proxies)
            print(res)
            return web.json_response(status=200,data=res)
        except Exception as e:
            err = str((type(e),e))
            print(err)
            data = {'status': 'unknown_err', 'cookies': [], 'err':err}
            return web.json_response(status=500, data=data)
    else:
        data = {'status': 'param_err', 'cookies': []}
        return web.json_response(status=500, data=data)