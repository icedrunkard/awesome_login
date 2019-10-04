# coding=utf-8
from aiohttp import web
from linkedin_login.handler import login as linkedin_login
from mail163_login.handler import login as mail163_login


async def index(request):
    text = '\tWELCOME!\n' \
           '\t./   GET: 当前页\n' \
           '\t./mail163_login   POST: 获取cookies\n' \
           '\tjson: {"username":"xxx@163.com","password":"xxxx"}\n' \
           '\t\tjson: {"username":"xxx@163.com","password":"xxxx","proxies":{"http":"http://ip:port"}}\n' \
           '\t./linkedin_login   POST: 获取cookies\n' \
           '\t\tjson: {"username":"xxxx","password":"xxxx","email":"xxxx","email_pwd":"xxxx"}\n' \
           '\t\tjson: {"username":"xxxx","password":"xxxx","email":"xxxx","email_pwd":"xxxx","proxies":{"http":"http://ip:port"}}\n'
    return web.Response(status=200, text=text)


if __name__ == '__main__':
    # docker run -e "MAX_CONCURRENT_SESSIONS=10" -e "PREBOOT_CHROME=true" -e "KEEP_ALIVE=true" -p 4001:3000 --restart always -d --name browserless browserless/chrome
    app = web.Application()
    routes = [
        web.get('/', index),
        web.post('/linkedin_login', linkedin_login),
        web.post('/mail163_login', mail163_login),
    ]
    app.add_routes(routes)
    print('listening port 4002...')
    web.run_app(app, port=4002)
