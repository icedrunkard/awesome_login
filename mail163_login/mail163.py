# coding=utf-8
# python 3.7
from util.preload import *
from util.settings import *
import asyncio
import pyppeteer
import random
import time
from PIL import Image
from io import BytesIO
from collections import defaultdict
from util.lianzhong import post_yzm_fail, get_click_coors

__author__ = 'icedrunkard'
# 控制并发度
semaphore = asyncio.Semaphore(CONCURRENT_TASKS_OR_FUTURES)


class Mail163:

    def __init__(self, username: str, password: str, proxies=None, is_mobile=True, engine=PYPPETEER_ENGINE):
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert len(username) and len(password)
        self.username = username
        self.password = password
        self.options = self.handled_options(proxies, engine)
        self.is_mobile = is_mobile
        self._frame = None
        self._frame_name = None

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
    async def res_from_instance(cls, username, password, proxies=None, is_mobile=IS_MOBILE, engine=PYPPETEER_ENGINE):
        mail_instance = cls(username, password, proxies=proxies, is_mobile=is_mobile, engine=engine)
        return await mail_instance.start()

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
        self.page.setDefaultNavigationTimeout(30000)
        for _p in await self.browser.pages():
            if _p != self.page:
                await _p.close()
        await self.injectjs()
        await self.page.setViewport(viewport={'width': 800, 'height': 800, 'isMobile': self.is_mobile})
        print('is_mobile: ', self.is_mobile)
        print(USER_AGENT)

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
        await self.page.setUserAgent(USER_AGENT)

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

    async def open(self):
        """
        打开浏览器
        :return:
        """
        if not self.is_mobile:
            url = 'https://mail.163.com/'
        else:
            url = 'https://smart.mail.163.com/login.htm'
        await self.page.goto(url)
        await self.page.waitForSelector('#normalLoginTab')
        t = await self.page.querySelector('#normalLoginTab')
        # 默认是二维码登录模式，需要切换
        display = await self.page.evaluate('document.querySelector("#normalLoginTab").getAttribute("style")')
        if isinstance(display, str) and 'none' in display:
            await self.page.click('#lbNormal')
        display = await self.page.evaluate('document.querySelector("#normalLoginTab").getAttribute("style")')
        assert 'block' in display
        print(await self.page.title())

    async def input(self):
        """
        输入用户名和密码
        :return:
        """
        for _frame in self.page.frames:
            if 'x-URS-iframe' in _frame.name:
                self._frame = _frame
                self._frame_name = _frame.name.replace('.', '\\.')
                break
        if not self._frame:
            return
        await self._frame.type('.j-inputtext.dlemail', self.username, {'delay': random.randint(20, 50)})
        await self._frame.type('.dlpwd', self.password, {'delay': random.randint(20, 50)})

    async def click_login_and_navigate(self):
        tasks_navigate = [
            asyncio.ensure_future(self._frame.click('#dologin')),
            asyncio.ensure_future(self.page_waitForNavigation()),
        ]
        await asyncio.wait(tasks_navigate)

    async def press_submit_btn(self):
        """
        按下登录键，可能出现验证码也可能登录成功
        :return: str:'login_success','captcha',None
        """
        # 此处如果没有验证码：如果有wait_yidun,程序出错；如果wait_success_panel,登录极快,可以加速登录过程
        # 此处如果有验证码：如果有wait_yidun,不会出错，很快进入下一步； 如果wait_success_panel,需要等到超时才会停止
        futures = [
            asyncio.ensure_future(self.click_login_and_navigate()),
            asyncio.ensure_future(self.wait_success_panel()),
            asyncio.ensure_future(self.wait_yidun()),
            asyncio.ensure_future(self.wait_pwd_err()),
        ]
        done, pending = await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)
        print(done)
        print(pending)
        results = defaultdict(list)
        for future in pending:
            name = future._coro.__name__
            results['pending'].append(name)
            future.cancel()
        for future in done:
            name = future._coro.__name__
            value = future.result()
            results['done'].append({name: value})
        if len(results['done']) == 1 and 'wait_success_panel' in results['done'][0]:
            print(results['done'][0]['wait_success_panel'])
            return 'login_success'
        elif len(results['done']) == 1 and 'wait_pwd_err' in results['done'][0]:
            return 'pwd_err'
        else:
            return 'captcha'

    async def wait_success_panel(self):
        """
        等待是否成功进入收件箱页面
        :return:
        """
        await self.page.waitForXPath('//*[@id="dvNavTitle"]', {'timeout': 20e3})
        await self.page.waitFor(500)
        return 'login_success'

    async def wait_yidun(self):
        """
        等待是否有网易验证码出现
        :return:
        """
        await self.page.waitForRequest(lambda req: req.url.startswith('https://webzjcaptcha.reg.163.com') and
                                                   req.method == 'GET')

    async def wait_pwd_err(self):
        """
        等待是否是密码错误
        :return:
        """
        r = await self.page.waitForResponse(lambda req: 'dl.reg.163.com/dl/l' in req.url)
        try:
            res = await r.text()
            if '413' in res:
                return 'pwd_err'
            else:
                await self.page.waitFor(15e3)
        except:
            await self.page.waitFor(15e3)

    async def yidun_cracked(self):
        await self._frame.waitForXPath('//*[contains(@id,"auto-id")][contains(text(),"验证成功")]')
        print('yidun cracked')

    async def _get_screenshot(self, fullscreenshot_abspath='fullscreen.png'):
        """
        获取网页截图
        :return: 网页截图对象
        """
        # refresh_btn_s = 'div.yidun_refresh'
        # yidun_refresh_btn = await self._frame.waitForSelector(refresh_btn_s)
        # await yidun_refresh_btn.click()
        yidun_bar_selector = '#ScapTcha > div > div.yidun_control > div.yidun_tips'
        yidun_panel = await self._frame.waitForSelector(yidun_bar_selector)
        if yidun_panel:
            await self._frame.hover(yidun_bar_selector, )
            await self._frame.waitForXPath('//*[contains(@id,"auto-id")][contains(text(),"依次点击")]')
            await self._frame.waitFor(1e3)
            screenshot = await self.page.screenshot()
            screenshot = Image.open(BytesIO(screenshot))
            screenshot.save(fullscreenshot_abspath)
            await self.page.waitFor(500)
            return screenshot

    async def _get_captcha_pos(self):
        """
        获取yidun验证码的边界坐标
        :return:
        """
        el = await self._frame.waitForXPath('//*[@id="ScapTcha"]')
        img = await self._frame.waitForXPath('//*[@id="ScapTcha"]/div/div[1]')
        # 等待图片被js加载
        await self.page.waitFor(500)
        img_height = (await img.boundingBox())['height']
        location = await el.boundingBox()
        top, bottom = location['y'] - img_height, location['y'] + location['height']
        left, right = location['x'], location['x'] + location['width']
        pos = (int(top), int(bottom), int(left), int(right))
        print('img pos:', str(pos))
        return pos

    async def get_captcha_buffer(self, fullimg_abspath='yidun.png'):
        """
        获取验证码图片
        :param fullimg_abspath: 图片名称
        :return: 验证码图片
        """
        screenshot = await self._get_screenshot()
        if screenshot:
            top, bottom, left, right = await self._get_captcha_pos()
            # print('验证码位置',top,bottom,left,right)
            captcha = screenshot.crop((left, top, right, bottom))
            captcha.save(fullimg_abspath)
            await self.page.waitFor(500)
            return captcha, (top, bottom, left, right)
        else:
            return None, None

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

    async def crack_captcha(self):
        """
        截图，然后联众打码
        TODO: 验证码刷新失败的情况
        :return:
        """
        captcha, pos = await self.get_captcha_buffer()
        if captcha is None:
            return
        obj = get_click_coors(file_name='yidun.png')
        if obj is None:
            print('post failed')
            return
        elif obj == 'jsdamaERR':
            print('打码错误')
            return
        assert isinstance(obj, dict)
        coors = obj['coors']
        yzm_id = obj['_id']
        top, bottom, left, right = pos
        for i, each in enumerate(coors):
            # 要有鼠标移动的轨迹
            if i == 0:
                # await self.page.mouse.click(left + each[0], top + each[1], {'delay': random.randint(30, 80)})
                start_coor = left + 5, top + 5
                end_coor = left + each[0], top + each[1]
                await self.mouse_click_with_trace(start_coor=start_coor, end_coor=end_coor)
            else:
                start_coor = left + coors[i - 1][0], top + coors[i - 1][1]
                end_coor = left + each[0], top + each[1]
                if 0 < i < len(coors):
                    await self.mouse_click_with_trace(start_coor=start_coor, end_coor=end_coor)
                else:
                    tasks = [
                        asyncio.ensure_future(self.mouse_click_with_trace(start_coor=start_coor, end_coor=end_coor)),
                        asyncio.ensure_future(self.page_waitForNavigation())
                    ]
                    await asyncio.wait(tasks)

        futures = [
            asyncio.ensure_future(self.wait_yidun()),
            asyncio.ensure_future(self.yidun_cracked())
        ]
        results = defaultdict(list)
        done, pending = await asyncio.wait(
            futures,
            return_when=asyncio.FIRST_COMPLETED
        )
        for future in pending:
            name = future._coro.__name__
            results['pending'].append(name)
            future.cancel()
        for future in done:
            name = future._coro.__name__
            results['done'].append(name)
        if 'yidun_cracked' in results['done']:
            return 'yidun_cracked'
        else:
            post_yzm_fail(yzm_id)
            # 考虑到 打码失败后， 验证码会自动刷新
            return await self.crack_captcha()

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
        await self.open()
        await self.input()
        res = await self.press_submit_btn()
        print('press_submit_btn status:', res)
        if res == 'login_success':
            cookiesld = await self.gen_all_cookies()
            await self.quit()
            obj = {'status': res, 'cookies': cookiesld}
            return obj
        # 一般用户名和密码正确的不需要验证码
        elif res == 'captcha':
            await self.quit()
            obj = {'status': res, 'cookies': []}
            return obj
        else:
            await self.quit()
            obj = {'status': 'pwd_err', 'cookies': []}
            return obj

    def run(self):
        """实例启动"""
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(self.start())
        loop.run_until_complete(task)


async def main(profiles):
    tasks = [
        asyncio.ensure_future(Mail163.res_from_instance(each['uname'], each['pwd'])) for each in profiles
    ]
    await asyncio.wait(tasks)


if __name__ == '__main__':
    profiles = [
        {'uname': 'xxxxxxx', 'pwd': 'xxxxxx'},
        # {'uname': 'icedrunkard', 'pwd': '1234567'},  # 异常帐号
    ]
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main(profiles))
    loop.run_until_complete(task)
