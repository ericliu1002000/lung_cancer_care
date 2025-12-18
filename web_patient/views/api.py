from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST
from health_data.services.health_metric import HealthMetricService
from users.decorators import auto_wechat_login, check_patient
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@auto_wechat_login
@check_patient
@require_POST
def delete_health_metric(request: HttpRequest) -> JsonResponse:
    """
    删除健康指标记录接口
    POST /p/api/health/metric/delete/
    """
    metric_id = request.POST.get('id')
    
    if not metric_id:
        return JsonResponse({'success': False, 'message': '参数错误'})
        
    try:
        HealthMetricService.delete_metric(int(metric_id))
        return JsonResponse({'success': True, 'message': '删除成功'})
    except Exception as e:
        logger.error(f"删除健康指标失败: {e}")
        return JsonResponse({'success': False, 'message': '删除失败'})

@auto_wechat_login
@check_patient
@require_POST
def update_health_metric(request: HttpRequest) -> JsonResponse:
    """
    更新健康指标记录接口
    POST /p/api/health/metric/update/
    """
    metric_id = request.POST.get('id')
    
    if not metric_id:
        return JsonResponse({'success': False, 'message': '参数错误'})
        
    try:
        # 获取需要更新的字段
        value_main = request.POST.get('value_main')
        value_sub = request.POST.get('value_sub')
        
        # 构造更新参数
        kwargs = {}
        if value_main is not None:
            kwargs['value_main'] = Decimal(value_main)
        if value_sub is not None:
            kwargs['value_sub'] = Decimal(value_sub)
            
        metric = HealthMetricService.update_manual_metric(int(metric_id), **kwargs)
        
        # 返回更新后的数据供前端刷新
        return JsonResponse({
            'success': True, 
            'message': '更新成功',
            'data': {
                'value_display': metric.display_value,
                'value_main': metric.value_main,
                'value_sub': metric.value_sub
            }
        })
    except Exception as e:
        logger.error(f"更新健康指标失败: {e}")
        return JsonResponse({'success': False, 'message': f'更新失败: {str(e)}'})
