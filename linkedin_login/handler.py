# coding=utf-8
from aiohttp import web
import json
from .linkedin import Linkedin


async def login(request):
    try:
        obj = await request.json()
    except:
        text = await request.text()
        try:
            obj = json.loads(text)
        except:
            obj = None
    print(obj)
    if isinstance(obj, dict) and obj.get('username') and obj.get('password') \
            and obj.get('email') and obj.get('email_pwd'):
        username = obj.get('username')
        password = obj.get('password')
        email = obj.get('email')
        email_pwd = obj.get('email_pwd')
        proxies = obj.get('proxies')
        try:
            cookiesld = await Linkedin.res_from_instance(username, password, email, email_pwd, proxies=proxies)
            print(cookiesld)
            if isinstance(cookiesld, list):
                text = json.dumps(cookiesld, ensure_ascii=False)
                return web.Response(status=200, text=text)
            return web.Response(status=500, text=str(cookiesld))
        except Exception as e:
            print(e)
            return web.Response(status=500, text=str(e))
    else:
        return web.Response(status=403, text='参数错误')