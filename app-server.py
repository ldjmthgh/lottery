import json
import os
import time
import secrets

import pandas as pd
import requests
from easydict import EasyDict as edict

from config import app_config
import random

from flask import Flask, Response

app = Flask("easy-lottery", static_folder=app_config.static_folder,
            template_folder=app_config.template_folder)


def build_res(code: int, msg: str, data: object = None):
    return Response(json.dumps({
        'code': code,
        'msg': msg,
        'data': data
    }), mimetype='application/json')


def init():
    """
    用于初始化程序
    1. 下载或补全 彩票的历史记录
    2. 启动定时器去更新彩票
    :return:
    """
    cache_init = False
    if not os.path.exists(app_config.storage_url):
        try:
            os.makedirs(os.path.join(app_config.storage_url, '1'))
            os.makedirs(os.path.join(app_config.storage_url, '2'))
            cache_init = True
        except Exception as e:
            raise RuntimeError("创建文件夹失败，" + str(e))
    if not os.path.isdir(app_config.storage_url):
        raise RuntimeError("缓存路径异常，不为合规的文件目录")
    csv_info_dir = os.path.join(app_config.storage_url, 'dlt_record.json')
    if not os.path.exists(csv_info_dir):
        cache_init = True
    if cache_init:
        # 全量下载
        download_dlt()
    else:
        # 获取所有的数据
        single_re = single_request()
        with open(os.path.join(app_config.storage_url, 'dlt_record.json'), 'rb', encoding='utf-8') as f:
            content_json = json.load(f)
        # 小于等于的情况不考虑
        if int(single_re.get('latest_lottery_num')) > int(content_json['latest_lottery_num']):
            # 补全  json 不管  可自行处理
            append_arr = []
            for item in single_re.get('values'):
                if item[0] > int(content_json['latest_lottery_num']):
                    append_arr.append(item)
            # 将列表转换为DataFrame
            columns = ['lotteryDrawNum', 'lotteryDrawResult', 'lotteryDrawTime']
            df = pd.DataFrame(append_arr, columns=columns)
            df2 = pd.read_csv(os.path.join(app_config.storage_url, '1.csv'))
            df3 = df.append(df2, ignore_index=True)
            # 按 'Score' 列降序排序
            sorted_df = df3.sort_values(by='lotteryDrawNum', ascending=False)
            sorted_df.to_csv(os.path.join(app_config.storage_url, '1.csv'), index=False)


def download_dlt():
    """
    大乐透下载
    :return:
    """
    # 增加header 防止403
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    headers = {
        'User-Agent': user_agent
    }
    last_page_reached = False
    index = 0
    csv_data = []
    csv_info = edict()
    while not last_page_reached:
        # 防止403
        time.sleep(0.5)
        index = index + 1
        download_url = app_config.base_url + '?gameNo=85&provinceId=0&pageSize=30&isVerify=1&pageNo={}'.format(index)
        try:
            response = requests.get(download_url, headers=headers)
            # 检查响应状态码
            if response.status_code == 200:
                # 解析JSON数据
                data = response.json()
                if index == 1:
                    csv_info.latest_lottery_num = data['value']['lastPoolDraw']['lotteryDrawNum']
                    csv_info.latest_lottery_time = data['value']['lastPoolDraw']['lotteryDrawTime']
                # 是否是最后一页数据
                if len(data['value']['list']) < 30:
                    last_page_reached = True
                for item in data['value']['list']:
                    csv_data.append([int(item['lotteryDrawNum']), item['lotteryDrawResult'], item['lotteryDrawTime']])
                # 可不存储结果文件
                json_dir = os.path.join(app_config.storage_url, 'dlt_{}.json'.format(index))
                with open(json_dir, 'w', encoding='utf-8') as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
            else:
                print("请求失败：{}；index： {}".format(response.status_code, index))
        except Exception as e:
            print("异常：{}".format(str(e)))
            # 定义列名
    columns = ['lotteryDrawNum', 'lotteryDrawResult', 'lotteryDrawTime']
    # 将列表转换为DataFrame
    df = pd.DataFrame(csv_data, columns=columns)
    # 将DataFrame存储为CSV文件
    df.to_csv(os.path.join(app_config.storage_url, '1.csv'), index=False)
    csv_info.total_num = len(csv_data)
    # 存储结果文件
    with open(os.path.join(app_config.storage_url, 'dlt_record.json'), 'w', encoding='utf-8') as f:
        json.dump(csv_info, f, ensure_ascii=False, indent=4)


def single_request():
    default_url = app_config.base_url + '?gameNo=85&provinceId=0&pageSize=30&isVerify=1&pageNo=2'
    response = requests.get(default_url)
    csv_data = []
    # 检查响应状态码
    if response.status_code == 200:
        # 解析JSON数据
        data = response.json()
        for item in data['value']['list']:
            csv_data.append([int(item['lotteryDrawNum']), item['lotteryDrawResult'], item['lotteryDrawTime']])
        return edict({
            'latest_lottery_num': data['value']['lotteryDrawNum'],
            'latest_lottery_time': data['value']['lotteryDrawTime'],
            'values': csv_data
        })
    else:
        raise RuntimeError('请求失败：' + str(response.status_code))


def get_random_num():
    """
    随机排列
    :return:
    """
    arr = secrets.SystemRandom().sample(range(1, 35), 5)
    arr.sort()
    arr2 = secrets.SystemRandom().sample(range(1, 12), 2)
    arr2.sort()
    arr.extend(arr2)
    return arr


@app.route('/dlt', methods=['GET'])
def dlt():
    return build_res(200, '随机', get_random_num())


if __name__ == '__main__':
    init()
    print('---- server running ----')
    app.run(host=app_config.host, port=app_config.port, debug=app_config.debug)
