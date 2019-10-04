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
            text = json.dumps(res,ensure_ascii=False)
            return web.json_response(status=200,text=text)
        except Exception as e:
            err = str((type(e),e))
            print(err)
            text = json.dumps({'status': 'unknown_err', 'cookies': []},ensure_ascii=False)
            return web.json_response(status=500, text=text)
    else:
        text = json.dumps({'status': 'param_err', 'cookies': []}, ensure_ascii=False)
        return web.json_response(status=500, text=text)