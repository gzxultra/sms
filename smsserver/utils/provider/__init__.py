from smsserver.utils.provider.yunpian import YunPianV1Client
from smsserver.utils.provider.dahansantong import DahanSanTongClient
from smsserver.utils.provider.base import SMSSendFailed
from conf import Config


yunpianv1_client = YunPianV1Client(Config.YUNPIAN_APIKEY)
dahansantong_client = DahanSanTongClient(Config.DAHANSANTONG_ACCOUNT, Config.DAHANSANTONG_PASSWORD)


__all__ = ['SMSSendFailed', 'yunpianv1_client', 'dahansantong_client']
