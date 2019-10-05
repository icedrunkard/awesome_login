# coding=utf-8
# python 3.7
import asyncio
import pyppeteer
import random
import time
import requests
from aiohttp import ClientSession
from util.preload import *
from util.settings import *
from .tools import check_latest_linkedin_code

__author__ = 'icedrunkard'
# 控制并发度
semaphore = asyncio.Semaphore(CONCURRENT_TASKS_OR_FUTURES)


class Linkedin:

    def __init__(self, username: str, password: str, email: str, email_pwd: str, proxies=None,
                 is_mobile=LINKEDIN_IS_MOBILE, engine=PYPPETEER_ENGINE, mail_engine=MAIL163_ENGINE):
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
            '--window-size=900,900',
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
        mail_instance = cls(username, password, email, email_pwd, proxies=proxies)
        res = await mail_instance.start()
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

    async def get_page(self):
        self.page = await self.browser.newPage()
        await self.page.setBypassCSP(True)
        self.page.setDefaultNavigationTimeout(60000)
        for _p in await self.browser.pages():
            if _p != self.page:
                await _p.close()
        await self.injectjs()
        await self.page.setViewport(viewport={'width': 900, 'height': 900, 'isMobile': self.is_mobile})
        print('is_mobile: ', self.is_mobile)
        print(LINKEDIN_USER_AGENT)

    async def quit(self):
        if self.options.get('executablePath'):
            await self.browser.close()
            self.browser.process.terminate()
        else:
            await self.browser.disconnect()

    async def page_waitForNavigation(self, options=None):
        try:
            await self.page.waitForNavigation(options)
            return 'navigate_well'
        except pyppeteer.errors.TimeoutError:
            return 'navigate_failed'
        except Exception as e:
            return 'navigate_failed'

    async def injectjs(self):
        # webdriver
        await self.page.evaluateOnNewDocument(js0)
        # permission
        await self.page.evaluateOnNewDocument(js1)
        # language
        await self.page.evaluateOnNewDocument(js4)
        # languages
        await self.page.evaluateOnNewDocument(js5)
        # plugins
        await self.page.evaluateOnNewDocument(js7)
        # useragent
        await self.page.setUserAgent(LINKEDIN_USER_AGENT)

        if self.is_mobile:
            # platform
            await self.page.evaluateOnNewDocument(js2)
            # appVersion
            await self.page.evaluateOnNewDocument(js3)
        else:
            # platform
            await self.page.evaluateOnNewDocument(js2_pc)
            # appVersion
            await self.page.evaluateOnNewDocument(js3_pc)

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

    async def open(self):
        """
        打开浏览器
        :return:
        """
        if not self.is_mobile:
            url = 'https://www.linkedin.com/uas/login'
        else:
            url = 'https://www.linkedin.com/uas/login'
        lang_setting = {'name': 'lang', 'value': 'v=2&lang=zh-cn', 'domain': '.linkedin.com', 'path': '/'}
        await self.page.setCookie(lang_setting)
        await self.page.goto(url)
        await self.page.waitForSelector('#username')
        print(await self.page.title())

    async def input(self):
        """
        输入用户名和密码
        :return:
        """
        await self.page.type('#username', self.username, {'delay': random.randint(10, 20)})
        await self.page.type('#password', self.password, {'delay': random.randint(10, 20)})

    async def input_checkcode(self, mail_cookies):
        assert isinstance(mail_cookies, list)
        cookiesd = {each['name']: each['value'] for each in mail_cookies}
        code = check_latest_linkedin_code(cookiesd, dtype='code')
        if not code:
            return
        await self.page.type('#input__email_verification_pin', code)
        await self.page.click('#email-pin-submit-button')
        await self.page.waitForNavigation()
        return await self._page_status()

    async def _page_status(self):
        # print('will wait 3s anyway...')
        # await self.page.waitFor(3e3)
        text = await self.page.content()
        # print(text)
        if '请进行快速的安全检查' in text:
            return 'captcha'
        elif '立即开始快速验证' in text and '出现异常登录' in text:
            return 'email_check'
        elif '您的帐号受到了限制' in text:
            return 'user_forbidden'
        elif '/voyager/api/identity/profiles' in text:
            url = 'https://www.linkedin.com/in/yiming-zhang-7a7841b/'
            tasks_check = [
                asyncio.ensure_future(self.page.goto(url)),
                asyncio.ensure_future(self.page.waitForNavigation()),
            ]
            done, pending = await asyncio.wait(tasks_check)
            for each in done:
                if each.exception():
                    print(each._coro.__name__, each.exception())
            return 'login_success'
        elif 'check/manage-account' in self.page.url:
            btn = await self.page.waitForSelector('#password-prompt-wrapper > button')
            await btn.click()
            await self.page.waitForRequest(lambda r: '/voyager/api/' in r.url)
            url = 'https://www.linkedin.com/in/yiming-zhang-7a7841b/'
            tasks_check = [
                asyncio.ensure_future(self.page.goto(url)),
                asyncio.ensure_future(self.page.waitForNavigation()),
            ]
            done, pending = await asyncio.wait(tasks_check)
            for each in done:
                if each.exception():
                    print(each._coro.__name__, each.exception())
            return 'login_success'
        else:
            try:
                uname_el = await self.page.querySelector('#username')
            except Exception as e:
                err = (type(e), e)
                print(err)
                print('unknown_status_1')
                return 'unknown_status_1'
            if uname_el:
                uname_err_cls_name = await self.page.evaluate("document.querySelector('#error-for-username').className")
                pwd_err_cls_name = await self.page.evaluate("document.querySelector('#error-for-password').className")
                print(type(uname_err_cls_name), uname_err_cls_name)
                if 'hidden' not in uname_err_cls_name:
                    return 'uname_err'
                elif 'hidden' not in pwd_err_cls_name:
                    return 'pwd_err'
                else:
                    print('unknown_status_2')
                    return 'unknown_status_2'
            else:
                print('unknown_status_3')
                return 'unknown_status_3'

    async def page_status(self):
        t0 = time.time()
        while time.time() - t0 < 90:
            try:
                _page_status = await self._page_status()
                if _page_status in ['login_success', 'email_check','user_forbidden']:
                    await asyncio.sleep(3)
                    return _page_status
            except Exception as e:
                print('page_status:',type(e),e,)
                await asyncio.sleep(3)

    async def res_after_click_login(self):
        if self.is_mobile:
            btn_selector = '#app__container > main > div > div.main-content__wrapper--mobile > form > div.login__form_action_container > button'
        else:
            btn_selector = '#app__container > main > div > form > div.login__form_action_container > button'
        tasks_navigate = [
            asyncio.ensure_future(self.page.click(btn_selector)),
            asyncio.ensure_future(self.page.waitForNavigation()),
        ]
        done, pending = await asyncio.wait(tasks_navigate)
        for each in done:
            if each.exception():
                print(each._coro.__name__, each.exception())
        page_status = await self.page_status()
        return page_status

    async def gen_all_cookies(self):
        try:
            resp = await self.page._client.send('Network.getAllCookies', {})
            cookiesld = resp.get('cookies', {})
            print(cookiesld)
            return cookiesld
        except Exception as e:
            print(type(e), e)

    async def start(self):
        # get_browser放在这里是为了可以实现有proxy功能
        await self.get_browser()
        await self.get_page()
        # await self.page.waitFor(10e3)
        await self.open()
        await self.input()
        page_status = await self.res_after_click_login()
        print('after click:', page_status)
        # await self.page.waitFor(1000e3)
        if page_status == 'login_success':
            cookiesld = await self.gen_all_cookies()
            await self.quit()
            obj = {'status': page_status, 'cookies': cookiesld}
            return obj
        elif page_status == 'email_check':
            payload = {"username": self.email, "password": self.email_pwd, "proxies": self.proxies}
            print('need to login mail:',self.mail_engine,payload)
            try:
                async with ClientSession() as session:
                    r = await session.request(method='POST',url=self.mail_engine,json=payload)
                    mail_obj = await r.json()
            except Exception as e:
                err = str((type(e), e))
                print(err)
                obj = {'status': 'mail_err_' + err, 'cookies': []}
                return obj

            # 需要邮箱验证码
            mail_status = mail_obj['status']
            mail_cookies = mail_obj['cookies']
            if mail_status == 'login_success':
                _page_status = await self.input_checkcode(mail_cookies)
                if _page_status == 'login_success':
                    cookiesld = await self.gen_all_cookies()
                    await self.quit()
                    obj = {'status': _page_status, 'cookies': cookiesld}
                    return obj
                else:
                    await self.quit()
                    obj = {'status': _page_status, 'cookies': []}
                    return obj
            else:
                status = 'mail_' + mail_status
                obj = {'status': status, 'cookies': []}
                return obj
        else:
            await self.quit()
            obj = {'status': page_status, 'cookies': []}
            return obj

    def run(self):
        """实例启动"""
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.start())
        loop.run_until_complete(task)


async def main(profiles):
    tasks = [
        asyncio.ensure_future(
            Linkedin.res_from_instance(
                each['uname'], each['pwd'], each['email'], each['email_pwd'])
        ) for each in profiles
    ]
    await asyncio.wait(tasks)


if __name__ == '__main__':
    profiles = [
        # {'uname': 'icedrunker@163.com', 'pwd': '*****'},  # 帐号被限制
        {'uname': 'xxxxx', 'pwd': 'xxxxx',
         'email': 'xxxxx', 'email_pwd': 'xxxxx'},  # 登录异常，要验证邮箱
        # {'uname': 'xxxxxx', 'pwd': 'xxxxxxxxx'},  # 密码不对
        # {'uname': '1234567@163.com', 'pwd': '1234567'},  # 异常帐号,captcha
        # {'uname': '1234567', 'pwd': '1234567'},  # 异常帐号,用户名格式不对
    ]
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(profiles))
    loop.run_until_complete(task)
