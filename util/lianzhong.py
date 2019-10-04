# coding=utf-8
import requests
from .settings import LIANZHONG_USERNAME,LIANZHONG_PWD


def get_click_coors(file_name='yidun.png'):
    """
    获取验证码图片点击坐标
    :return: 验证码图片
    """
    api_username = LIANZHONG_USERNAME  # qwer
    api_password = LIANZHONG_PWD  # 1234
    yzm_type = '1303'
    files = {'upload': (file_name, open(file_name, 'rb'), 'image/png')}
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
        'Connection': 'keep-alive',
        'Host': 'v1-http-api.jsdama.com',
        'Upgrade-Insecure-Requests': '1'
    }
    data = {
        'user_name': api_username,
        'user_pw': api_password,
        # 'yzm_minlen': yzm_min,
        # 'yzm_maxlen': yzm_max,
        'yzmtype_mark': yzm_type,
        # 'zztool_token': tools_token
    }
    # {"data":{"val":"156,204|456,604","id":31909022682},"result":true}
    for retry in range(3):
        try:
            r = requests.post('http://v1-http-api.jsdama.com/api.php?mod=php&act=upload',
                              headers=headers, data=data, files=files, verify=False)
            print(r.text)
            _obj = r.json()
            if isinstance(_obj['data'], dict):
                coors = [(int(each.split(',')[0]), int(each.split(',')[1])) for each in
                         _obj['data']['val'].split('|')]
                obj = {'_id': _obj['data']['id'], 'coors': coors}
                return obj
            else:
                return 'jsdamaERR'
        except Exception as e:
            print(type(e), e)
            if retry>=2:
                return


def post_yzm_fail(yzm_id):
    """
    上传验证码图篇错误的信息
    :param yzm_id: 验证码种类，也是图片名称
    :return: None
    """
    api_username = LIANZHONG_USERNAME
    api_password = LIANZHONG_PWD
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0',
        # 'Content-Type': 'multipart/form-data; boundary=---------------------------227973204131376',
        'Connection': 'keep-alive',
        'Host': 'v1-http-api.jsdama.com',
        'Upgrade-Insecure-Requests': '1'
    }
    data = {
        'user_name': api_username,
        'user_pw': api_password,
        'yzm_id': yzm_id,
    }
    try:
        r = requests.post('http://v1-http-api.jsdama.com/api.php?mod=php&act=error',
                          headers=headers, data=data, verify=False)
        print('yzm failed:', r.text)
    except Exception as e:
        print(type(e), e)