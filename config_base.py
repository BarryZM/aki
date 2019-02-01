from os import path

from nonebot.default_config import *

NICKNAME = ['奶茶', '小奶茶']
COMMAND_START = {'', '/', '!', '／', '！'}
COMMAND_SEP = {'/', '.'}
SESSION_RUN_TIMEOUT = timedelta(seconds=20)

# 用户取消交互时的回复
SESSION_CANCEL_EXPRESSION = (
    '好的',
    '好的吧',
    '好吧，那奶茶就不打扰啦',
    '那奶茶先不打扰小主人啦',
)

# 数据文件夹
DATA_FOLDER = path.join(path.dirname(__file__), 'data')

# 数据库 URL
DATABASE_URL = ''

# 消息采集器 dump 频率
MESSAGE_COLLECTOR_DUMP_FREQ = 'H'

# aiocache 配置
AIOCACHE_DEFAULT_CONFIG = {
    'cache': 'aiocache.SimpleMemoryCache',
    'serializer': {
        'class': 'aiocache.serializers.PickleSerializer'
    }
}

# 使用手册图片地址
MANUAL_IMAGE_URL_FORMAT = 'https://raw.githubusercontent.com/cczu-osa/aki/master/manual/screenshots/{}.png'

# 允许和炸毛互动的群
GROUPS_TO_PLAY_WITH_ZHAMAO = []

# 百度 AIP
BAIDU_AIP_APP_ID = ''
BAIDU_AIP_API_KEY = ''
BAIDU_AIP_SECRET_KEY = ''

# 语言云
LTP_CLOUD_API_KEY = ''

# 图灵机器人
TULING_API_KEY = ''

# 聚合数据
JUHE_JOKE_API_KEY = ''  # 笑话大全
JUHE_IDIOM_API_KEY = ''  # 成语词典

# 抢红包功能临时数据
RED_PACKET = 0  # 本次抢红包的剩余金额数
PER_COINS = {}  # 本次抢红包临时记录
