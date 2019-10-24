# coding=utf-8
import re
import requests
import time
import json
from util.settings import USER_AGENT
from typing import Union


def check_latest_linkedin_code(cookiesd: dict, dtype='code') -> Union[None, str]:
    sid = cookiesd.get('Coremail.sid')
    if not sid:
        print('登录失败')
        return
    """
    检查最新邮件是否有领英验证码
    :param cookiesd: 登录163邮箱的cookies，dict类型
    :param dtype: 验证码是数字类型还是链接
    :return:
    """
    url = f'https://mail.163.com/js6/s?sid={sid}&func=mbox:listMessages&mbox_folder_enter=1'
    session = requests.Session()
    # 此方法可以保持cookies
    session.cookies.update(cookiesd)
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            code = code_from_session_post(session, url, dtype=dtype)
            if code == 'code_not_arrived':
                continue
            return code
        except Exception as e:
            err = (type(e), e)
            print(err)
            time.sleep(3)


def code_from_session_post(session, url, dtype='code') -> Union[str, None]:
    print('session posting...')
    headers = {
        'Accept': 'text/javascript',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-type': 'application/x-www-form-urlencoded',
        'DNT': '1',
        'Host': 'mail.163.com',
        'Origin': 'https://mail.163.com',
        'User-Agent': USER_AGENT
    }
    data = {
        'var': """<?xml version="1.0"?><object><int name="fid">1</int><string name="order">date</string><boolean name="desc">true</boolean><int name="limit">20</int><int name="start">0</int><boolean name="skipLockedFolders">false</boolean><string name="topFlag">top</string><boolean name="returnTag">true</boolean><boolean name="returnTotal">true</boolean></object>"""
    }

    def to_ts(matched):
        """
        将符合正则的时间字符串转换成时间戳
        :param matched: 正则obj
        :return: int
        """
        datestr = matched.group().replace('new Date', '')
        datearr = list(eval(datestr))
        datearr[1] += 1
        datearr.extend([0, 0, 0])
        datetup = tuple(datearr)
        ts = str(int(time.mktime(datetup)))
        return ts

    r = session.post(url, headers=headers, data=data)
    text = r.text.replace('"', '_')
    text = re.sub('new Date\((.*?)\)', to_ts, text)
    text = text.replace("'", '"')
    obj = json.loads(text)['var'][0]
    sender = obj['from']
    timestamp = obj['receivedDate']
    title = obj['subject']
    mid = obj['id']
    res = {'sender': sender, 'time': timestamp, 'title': title, 'mid': mid}
    print('收件箱首行', res)
    if dtype == 'code':
        code_r = re.search('\d{6}', title)
        # 有6位 验证码的 ，继续
        if code_r:
            if '领英' not in sender:
                # 标题没有领英，说明不是领英验证码
                return
            elif timestamp < time.time()-60:
                print('验证码还没到，请稍后再试')
                return 'code_not_arrived'
            else:
                print('标题中验证码：', code_r.group())
                return code_r.group()
        # 没有6位数字的 要到详情页面取
        url = f'https://mail.163.com/js6/read/readhtml.jsp?mid={mid}'
        _headers = headers.copy()
        _headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
        _headers.pop('Content-type')
        r_detail = session.get(url, headers=_headers, )
        text = r_detail.text.replace('"', '_')
        code_r = re.search('请用此验证码完成登录步骤.{0,20}(\d{6})', text)
        # 页面中有数字验证码
        if code_r:
            if '领英' not in text:
                # 页面没有领英，说明不是领英验证码
                return
            else:
                print('页面中验证码：', code_r.group(1))
                return code_r.group(1)
        # 页面中没有数字验证码
        print('no_code')
        return
    else:
        url = f'https://mail.163.com/js6/read/readhtml.jsp?mid={mid}'
        _headers = headers.copy()
        _headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'
        _headers.pop('Content-type')
        r_detail = session.get(url, headers=_headers)
        text = r_detail.text.replace('"', '_')
        res = re.search('https://www.linkedin.com/comm/psettings(.*)(?=\n)', text)
        if res:
            print('check_url:', res.group())
            return res.group()
        print('no check_url')
        return
