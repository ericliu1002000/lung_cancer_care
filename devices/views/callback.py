import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from devices.service.smartwatch import SmartWatchService

logger = logging.getLogger(__name__)

@csrf_exempt  # 必须免除 CSRF，因为是外部服务器调用
def smartwatch_data_callback(request):
    if request.method != 'POST':
        return JsonResponse({'errorCode': 1, 'msg': 'Method not allowed'})

    # 1. 安全验证 (签名校验)
    if not SmartWatchService.verify_callback_signature(request):
        return JsonResponse({'errorCode': 1, 'msg': 'Signature verification failed'})

    try:
        # 2. 解析数据 [cite: 56]
        data = json.loads(request.body)
        event_type = data.get('eventType')
        payload = data.get('data', {})
        
        logger.info(f"收到手表数据回调: Type={event_type}, Data={payload}")

        # 3. 业务处理
        # eventType: 1 代表手表数据 [cite: 76]
        if event_type == 1:
            device_no = payload.get('deviceNo')
            record_time = payload.get('recordTime')
            
            # 这里可以根据 type 字段判断是哪种数据 [cite: 89, 146]
            data_type = payload.get('type') # WATCH, BPG, PO, WS
            
            if data_type == 'BPG': # 血压 [cite: 186]
                 bpg_data = payload.get('bpgData', {})
                 sbp = bpg_data.get('sbp') # 收缩压
                 dbp = bpg_data.get('dbp') # 舒张压
                 # TODO: 保存到你的数据库
                 print(f"设备{device_no} 上传血压: {sbp}/{dbp} at {record_time}")
            
            elif data_type == 'WATCH': # 心率/计步 [cite: 153]
                 watch_data = payload.get('watchData', {})
                 # ...处理心率等
            
        # 4. 返回成功响应 [cite: 68]
        return JsonResponse({'errorCode': 0, 'msg': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'errorCode': 1, 'msg': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"处理回调异常: {e}")
        return JsonResponse({'errorCode': 1, 'msg': 'Internal Error'})