import configparser

from easydict import EasyDict as edict

app_config = edict()
# 创建一个ConfigParser对象
config = configparser.ConfigParser()
# 读取ini文件
config.read('config.ini')

# 获取配置信息
# common
app_config.storage_url = config.get('common', 'storage_url')
app_config.base_url = config.get('common', 'base_url')
app_config.worker_num = config.getint('common', 'worker_num')
# flask
app_config.static_folder = config.get('flask', 'static_folder')
app_config.template_folder = config.get('flask', 'template_folder')
app_config.static_folder = config.getboolean('flask', 'debug')
app_config.static_folder = config.get('flask', 'host')
app_config.static_folder = config.getint('flask', 'port')
