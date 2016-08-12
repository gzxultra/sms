# coding: utf-8
from smsserver.utils.provider.yunpian import YunPianV1Client
from smsserver.utils.provider.dahansantong import DahanSanTongClient
from smsserver.utils.provider.alidayu import ALiDaYuClient
from smsserver.utils.provider.base import SMSSendFailed
from conf import Config


yunpianv1_client = YunPianV1Client(Config.YUNPIAN_APIKEY)
dahansantong_client = DahanSanTongClient(Config.DAHANSANTONG_ACCOUNT, Config.DAHANSANTONG_PASSWORD)
alidayu_client = ALiDaYuClient(Config.ALIDAYU_KEY, Config.ALIDAYU_SECRET,
                               Config.ALIDAYU_TEMPLATES_DICT, Config.ALIDAYU_CALLED_SHOW_NUM)

__all__ = ['SMSSendFailed', 'yunpianv1_client', 'dahansantong_client', 'alidayu_client']
