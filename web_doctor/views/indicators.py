from datetime import date, timedelta, datetime
from django.utils import timezone
from core.models import TreatmentCycle
from core.service.treatment_cycle import get_treatment_cycles
from health_data.services.health_metric import HealthMetricService
from health_data.models.health_metric import MetricType
from users.models import PatientProfile

def build_indicators_context(
    patient: PatientProfile,
    cycle_id: str | None = None,
    start_date_str: str | None = None,
    end_date_str: str | None = None
) -> dict:
    """
    构建“患者指标”Tab 所需的上下文数据：
    - 查询近30天数据
    - 获取疗程列表
    """
    today = timezone.localdate()
    
    # 默认值：近30天
    start_date = today - timedelta(days=29)
    end_date = today
    
    is_default_view = True

    # 1. 优先使用自定义日期范围
    if start_date_str and end_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            is_default_view = False
        except ValueError:
            pass # 格式错误回退到默认
    
    # 2. 其次使用疗程范围
    elif cycle_id:
        try:
            cycle = TreatmentCycle.objects.get(pk=cycle_id, patient=patient)
            start_date = cycle.start_date
            end_date = cycle.end_date if cycle.end_date else today
            is_default_view = False
        except (TreatmentCycle.DoesNotExist, ValueError):
            pass

    # 3. 校验跨度（最大1年 = 366天）
    delta_days = (end_date - start_date).days
    if delta_days > 366:
        # 超过一年，强制截断为 start_date + 1年
        end_date = start_date + timedelta(days=365)
        delta_days = 365
    elif delta_days < 0:
        # 结束日期早于开始日期，重置为单日或默认
        end_date = start_date
        delta_days = 0

    # 构造查询用的 datetime (start 00:00:00 ~ end+1 00:00:00)
    # end_date 在界面上通常是包含的，所以查询时要加1天
    query_end_date = end_date + timedelta(days=1)
    
    start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_dt = timezone.make_aware(datetime.combine(query_end_date, datetime.min.time()))

    # 生成日期字符串列表 (MM-DD)
    # 如果跨年，可能需要显示年份，这里暂时保持 MM-DD，或者根据跨度决定
    date_fmt = "%m-%d"
    if start_date.year != end_date.year:
        date_fmt = "%Y-%m-%d"
        
    date_strs = [(start_date + timedelta(days=i)).strftime(date_fmt) for i in range(delta_days + 1)]

    # 1. 获取疗程列表
    cycles_page = get_treatment_cycles(patient, page=1, page_size=100)
    treatment_cycles = cycles_page.object_list

    # 2. 获取各指标数据
    charts = {}

    def get_daily_values(metric_type, value_key='value_main'):
        """获取指定指标范围内的每日数据（取每日最新一条）"""
        page = HealthMetricService.query_metrics_by_type(
            patient_id=patient.id,
            metric_type=metric_type,
            start_date=start_dt,
            end_date=end_dt,
            page_size=2000, # 足够大以覆盖数据
            sort_order='asc' # 按时间正序
        )
        
        data_map = {}
        for m in page.object_list:
            local_dt = timezone.localtime(m.measured_at)
            d_str = local_dt.strftime(date_fmt)
            val = getattr(m, value_key)
            if val is not None:
                data_map[d_str] = float(val)
        
        return [data_map.get(d, 0) for d in date_strs]

    # SpO2
    spo2_data = get_daily_values(MetricType.BLOOD_OXYGEN)
    charts['spo2'] = {
        "id": "chart-spo2",
        "title": "静息血氧 SpO2 (%)",
        "dates": date_strs,
        "series": [{"name": "静息血氧", "data": spo2_data, "color": "#3b82f6"}],
        "y_min": 80,
        "y_max": 100
    }

    # BP (需要主值和副值)
    bp_sbp = get_daily_values(MetricType.BLOOD_PRESSURE, 'value_main')
    bp_dbp = get_daily_values(MetricType.BLOOD_PRESSURE, 'value_sub')
    charts['bp'] = {
        "id": "chart-bp",
        "title": "血压 收缩压/舒张压 (mmHg)",
        "dates": date_strs,
        "series": [
            {"name": "收缩压", "data": bp_sbp, "color": "#3b82f6"},
            {"name": "舒张压", "data": bp_dbp, "color": "#10b981"}
        ],
        "y_min": 60,
        "y_max": 180
    }

    # Heart Rate
    hr_data = get_daily_values(MetricType.HEART_RATE)
    charts['hr'] = {
        "id": "chart-hr",
        "title": "静息心率 (次/min)",
        "dates": date_strs,
        "series": [{"name": "静息心率", "data": hr_data, "color": "#3b82f6"}],
        "y_min": 40,
        "y_max": 140
    }

    # Weight
    weight_data = get_daily_values(MetricType.WEIGHT)
    charts['weight'] = {
        "id": "chart-weight",
        "title": "体重 (KG)",
        "dates": date_strs,
        "series": [{"name": "体重", "data": weight_data, "color": "#3b82f6"}],
        "y_min": 40,
        "y_max": 120
    }

    # Temperature
    temp_data = get_daily_values(MetricType.BODY_TEMPERATURE)
    charts['temp'] = {
        "id": "chart-temp",
        "title": "体温 (℃)",
        "dates": date_strs,
        "series": [{"name": "体温", "data": temp_data, "color": "#3b82f6"}],
        "y_min": 35,
        "y_max": 42
    }

    # Steps
    steps_data = get_daily_values(MetricType.STEPS)
    charts['steps'] = {
        "id": "chart-steps",
        "title": "步数",
        "dates": date_strs,
        "series": [{"name": "步数", "data": steps_data, "color": "#3b82f6"}],
        "y_min": 0,
        "y_max": 15000 
    }

    # 3. 服药记录
    med_page = HealthMetricService.query_metrics_by_type(
        patient_id=patient.id,
        metric_type=MetricType.USE_MEDICATED,
        start_date=start_dt,
        end_date=end_dt,
        page_size=2000,
        sort_order='asc'
    )
    med_map = {}
    for m in med_page.object_list:
        local_dt = timezone.localtime(m.measured_at)
        d_str = local_dt.strftime(date_fmt)
        med_map[d_str] = True 

    medication_data = []
    med_count = 0
    for d in date_strs:
        taken = med_map.get(d, False)
        if taken:
            med_count += 1
        medication_data.append({
            "date": d,
            "taken": taken
        })
    
    total_days = len(date_strs)
    compliance = int((med_count / total_days) * 100) if total_days > 0 else 0

    return {
        "medication_data": medication_data,
        "medication_stats": {
            "count": med_count,
            "compliance": compliance
        },
        "charts": charts,
        "treatment_cycles": treatment_cycles,
        "dates": date_strs,
        # 回显当前的筛选条件
        "current_cycle_id": int(cycle_id) if cycle_id else "",
        # 如果是默认视图（未筛选），则不回填日期到 input，显示为空；否则回填
        "current_start_date": start_date.isoformat() if not is_default_view else "",
        "current_end_date": end_date.isoformat() if not is_default_view else "",
        "is_default_view": is_default_view,
    }
