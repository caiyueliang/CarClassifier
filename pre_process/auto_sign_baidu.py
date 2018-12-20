# coding:utf-8
import os
import urllib, urllib2, base64
import sys
import ssl
import json
import shutil
from retry import retry

my_access_token = ['24.486cc9beb6b983cc636628803b3618fa.2592000.1547862801.282335-15215859',
                   '24.2fff2efc449c47ac9eb011a106827629.2592000.1547865295.282335-15216921']


def get_access_token(api_key, secret_key):
    # client_id 为官网获取的AK， client_secret 为官网获取的SK
    host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=' + api_key + \
           '&client_secret=' + secret_key
    request = urllib2.Request(host)
    request.add_header('Content-Type', 'application/json; charset=UTF-8')
    response = urllib2.urlopen(request)
    content = response.read()
    if (content):
        print(content)


@retry(tries=3)
def post_image_base64_baidu(image_path, access_token):
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/car"

    # 二进制方式打开图片文件
    f = open(image_path, 'rb')
    img = base64.b64encode(f.read())

    params = {"image": img, "top_num": 5}
    params = urllib.urlencode(params)

    # access_token = '[调用鉴权接口获取的token]'
    request_url = request_url + "?access_token=" + access_token
    request = urllib2.Request(url=request_url, data=params)
    request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    response = urllib2.urlopen(request)
    content = response.read()
    print content

    if 'Open api daily request limit reached' in content:
        # access_token异常，次数超过，更换token
        return False, True, None
    if content:
        decode_json = json.loads(content)
        return True, False, decode_json

    return False, False, None


def auto_clean(root_path):
    for root, dirs, files in os.walk(root_path):
        for file in files:
            old_file_path = os.path.join(root, file)
            if '.jpg' not in file:
                new_file_name = file.replace('jpg', '.jpg')
                new_file_path = os.path.join(root, new_file_name)
                shutil.move(old_file_path, new_file_path)


# 自动标记
def auto_sign(root_path):
    use_token_id = 0

    for root, dirs, files in os.walk(root_path):
        for file in files:
            old_file_path = os.path.join(root, file)

            # 没有百度标志，表示没进行识别
            if '_baidu_' not in file:
                print old_file_path
                success, token_err, result = post_image_base64_baidu(old_file_path, my_access_token[use_token_id])
                while token_err:
                    if use_token_id < len(my_access_token) - 1:
                        use_token_id += 1
                        print('change token id to: %s' % my_access_token[use_token_id])
                        success, token_err, result = post_image_base64_baidu(old_file_path, my_access_token[use_token_id])
                    else:
                        print('[auto_sign] all access_token used !')
                        return

                if success:
                    year_0 = str(result['result'][0]['year']) if type(result['result'][0]['year']) == int else result['result'][0]['year'].encode('utf-8')
                    year_1 = str(result['result'][1]['year']) if type(result['result'][1]['year']) == int else result['result'][1]['year'].encode('utf-8')
                    new_file_name = file.split('.')[0] + '_baidu' + \
                                    '_' + result['result'][0]['name'].encode('utf-8') + \
                                    '_' + str(result['result'][0]['score']) + \
                                    '_' + year_0 + \
                                    '_' + result['result'][1]['name'].encode('utf-8') + \
                                    '_' + str(result['result'][1]['score']) + \
                                    '_' + year_1 + \
                                    '.' + file.split('.')[-1]
                    print(new_file_name)
                    new_file_path = os.path.join(root, new_file_name)
                    shutil.move(old_file_path, new_file_path)
                else:
                    new_file_name = file.split('.')[0] + '_baidu_None_0.0_0_None_0.0_0.' + file.split('.')[-1]
                    new_file_path = os.path.join(root, new_file_name)
                    shutil.move(old_file_path, new_file_path)


if __name__ == '__main__':
    # post_image_base64('http://127.0.0.1:9511')
    # post_image_base64('http://lpr.maysatech.com')

    # 调用百度接口
    # get_access_token('37UGKok26cBBSEDz9GCSi0p0', 'd1L9eWIPB2EftZGeEQcFmAYwsIveyvTl')
    # get_access_token('eRHDdhQhx6Mw7X1ZhwoG51Va', '2G4faO8HDgvwNlAML4KU9TtGrtkGms9c')
    # post_image_base64_baidu('./112.jpg', '24.486cc9beb6b983cc636628803b3618fa.2592000.1547862801.282335-15215859')

    # 自动标记
    # auto_clean('../../Data/car_classifier/clean_car/car_data')
    auto_sign('../../Data/car_classifier/clean_car/car_data')