# coding=utf-8
# python 3.7
from util.preload import *
from util.settings import *
import asyncio
import pyppeteer
from random import randint
import time
import warnings
from typing import Union

__author__ = 'icedrunkard'
# 控制并发度
semaphore = asyncio.Semaphore(CONCURRENT_TASKS_OR_FUTURES)


class BaseClient:

    def __init__(self, username: str, password: str, email: str = None, email_pwd: str = None, proxies=None,
                 is_mobile=IS_MOBILE, engine=PYPPETEER_ENGINE, mail_engine=MAIL163_ENGINE):
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert len(username) and len(password)
        self.username = username
        self.password = password
        self.email = email
        self.email_pwd = email_pwd
        self.proxies = proxies
        self.options = self.handled_options(proxies, engine)
        self.is_mobile = is_mobile
        self.mail_engine = mail_engine

    @staticmethod
    def handled_options(proxies, engine):
        args = [
            '--window-size=800,800',
            '--safebrowsing-disable-download-protection',
            '--no-sandbox',
        ]

        if isinstance(proxies, dict) and proxies.get('http'):
            proxy = "--proxy-server={}".format(proxies['http'])
            args.append(proxy)
        elif proxies is None:
            pass
        else:
            raise ValueError('proxies type should be dict or str')

        options = {
            'headless': True,
            'dumpio': True,
            "args": args,
            'logLevel': 'ERROR',
            'ignoreHTTPSErrors': True
        }
        if engine == BROWSERLESS_ENGINE:
            options['browserWSEndpoint'] = BROWSERLESS_ENGINE
        elif engine == LOCAL_ENGINE:
            options['executablePath'] = CHROME_EXEC_PATH
            options['headless'] = False if 'windows' in PLATFORM else True
        else:
            raise ValueError('chrome engine err, should be ws or local')
        return options

    @classmethod
    async def res_from_instance(cls, username, password, email, email_pwd, proxies=None):
        instance = cls(username, password, email, email_pwd, proxies=proxies)
        res = await instance.start()
        print(res)
        return res

    async def get_browser(self):
        print(self.options)
        if self.options.get('executablePath'):
            self.browser = await pyppeteer.launch(self.options)
        elif self.options.get('browserWSEndpoint'):
            self.browser = await pyppeteer.connect(self.options)
        else:
            raise ValueError('launch options ERR')
        print(self.browser.wsEndpoint)

    async def get_page(self,page_name='page'):
        _page = await self.browser.newPage()
        exec('self.{} = _page'.format(page_name))
        page = getattr(self,page_name)
        # if page_name == 'page':
        #     print(self.page)
        await page.setBypassCSP(True)
        page.setDefaultNavigationTimeout(30000)
        if page_name == 'page':
            for _p in await self.browser.pages():
                if _p != page:
                    await _p.close()
        await self.injectjs(page_name)
        await page.setViewport(viewport={'width': 800, 'height': 800, 'isMobile': self.is_mobile})
        print('is_mobile: ', self.is_mobile)
        print(USER_AGENT)

    async def injectjs(self,page_name='page'):
        page = getattr(self,page_name)
        # webdriver
        await page.evaluateOnNewDocument(js0)
        # permission
        await page.evaluateOnNewDocument(js1)
        # language
        await page.evaluateOnNewDocument(js4)
        # languages
        await page.evaluateOnNewDocument(js5)
        # plugins
        await page.evaluateOnNewDocument(js7)
        # useragent
        await page.setUserAgent(USER_AGENT)

        if self.is_mobile:
            # platform
            await page.evaluateOnNewDocument(js2)
            # appVersion
            await page.evaluateOnNewDocument(js3)
        else:
            # platform
            await page.evaluateOnNewDocument(js2_pc)
            # appVersion
            await page.evaluateOnNewDocument(js3_pc)

    async def quit(self):
        if self.options.get('executablePath'):
            await self.browser.close()
            self.browser.process.terminate()
        else:
            await self.browser.disconnect()

    async def mouse_click_with_trace(self, start_coor: tuple, end_coor: tuple, start_click=False):
        """
        模拟将鼠标坐标从起点坐标移动到终点坐标
        :param start_coor:
        :param end_coor: 终点坐标会单击
        :param start_click: 起始坐标处是否要单击
        :return:
        """
        now_x = start_coor[0]
        now_y = start_coor[1]
        mouse_x = end_coor[0]
        mouse_y = end_coor[1]
        if start_click:
            await self.page.mouse.click(now_x, now_y)

        k = (mouse_y - now_y) / (mouse_x - now_x) if mouse_x != now_x else None
        b = now_y - k * now_x if k is not None else None
        steps = 100
        if k is None:  # 斜率无穷大
            dy = (mouse_y - now_y) / steps
            t0 = time.time()
            now_x = mouse_x
            while abs(now_y + dy - mouse_y) > 1 and time.time() - t0 < 5:
                now_y = int(now_y + dy)
                await self.page.mouse.move(now_x, now_y)
        else:
            dx = (mouse_x - now_x) / steps
            t0 = time.time()
            while abs(now_x + dx - mouse_x) > 1 and time.time() - t0 < 5:
                now_x = int(now_x + dx)
                now_y = int(k * (now_x + dx) + b)
                await self.page.mouse.move(now_x, now_y)
        await self.page.mouse.click(mouse_x, mouse_y)

    async def gen_all_cookies(self):
        try:
            resp = await self.page._client.send('Network.getAllCookies', {})
            cookiesld = resp.get('cookies', {})
            # print(cookiesld)
            return cookiesld
        except Exception as e:
            print(type(e), e)

    async def start(self):
        await self.get_browser()
        await self.get_page()
        await self.page.waitFor(80e3)
        await self.page.goto('http://localhost:3000')
        await self.page.waitFor(5e3)
        print(await self.page.title())
        pass

    def run(self):
        """实例启动"""
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.start())
        loop.run_until_complete(task)


if __name__ == '__main__':
    client = BaseClient(username='1',password='2')
    client.run()
