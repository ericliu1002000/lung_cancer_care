from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from users.models import CustomUser

def record_temperature(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】体温录入页面 `/p/record/temperature/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 提交按钮（前端校验）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid
    }
    
    return render(request, "web_patient/record_temperature.html", context)

def record_steps(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】步数录入页面 `/p/record/steps/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 提交按钮（前端校验）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid
    }
    
    return render(request, "web_patient/record_steps.html", context)


def record_bp(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】血压心率录入页面 `/p/record/bp/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供收缩压、舒张压、心率输入框。
    4. 提交按钮（前端校验）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid
    }
    
    return render(request, "web_patient/record_bp.html", context)

def record_spo2(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】血氧饱和度录入页面 `/p/record/spo2/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供血氧饱和度输入框。
    4. 提交按钮（前端校验）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid
    }
    
    return render(request, "web_patient/record_spo2.html", context)

def record_weight(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】体重录入页面 `/p/record/weight/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供体重输入框。
    4. 提交按钮（前端校验）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid
    }
    
    return render(request, "web_patient/record_weight.html", context)

def record_breath(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】呼吸情况自测页面 `/p/record/breath/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供呼吸情况多选列表（数据由后端传入）。
    4. 提交按钮。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    # 呼吸情况选项数据
    breath_options = [
        {"value": "0", "label": "(0) 整体顺畅，仅剧烈运动气促"},
        {"value": "1", "label": "(1) 快走或上坡气促"},
        {"value": "2", "label": "(2) 与同龄人同走需停下"},
        {"value": "3", "label": "(3) 走100米或几分钟即停"},
        {"value": "4", "label": "(4) 静息或穿衣即气促"},
    ]

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid,
        "breath_options": breath_options
    }
    
    return render(request, "web_patient/record_breath.html", context)

def record_sputum(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】咳嗽与痰色情况自测页面 `/p/record/sputum/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供咳嗽情况（多选）和痰色情况（单选网格）。
    4. 提交按钮。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    # 咳嗽情况选项数据（多选）
    cough_options = [
        {"value": "0", "label": "(0) 今日无咳嗽"},
        {"value": "1", "label": "(1) 轻度/偶发"},
        {"value": "2", "label": "(2) 多次影响活动或夜间休息"},
        {"value": "3", "label": "(3) 持续或严重影响说话/睡眠"},
    ]

    # 痰色情况选项数据（单选网格）
    # color_class 用于前端显示颜色条或图标颜色
    sputum_colors = [
        {"value": "0", "label": "(0)无痰", "desc": "无痰/透明", "color_class": "bg-gray-100","color_hex": ""},
        {"value": "1", "label": "(1)白色", "desc": "较黏/浑白", "color_class": "bg-white border-gray-200","color_hex": "#FFFFFF"},
        {"value": "2", "label": "(2)黄色", "desc": "发黄/黏稠", "color_class": "bg-yellow-100 border-yellow-200","color_hex": "#FACC15"},
        {"value": "3", "label": "(3)绿色", "desc": "发绿/黏稠", "color_class": "bg-green-100 border-green-200","color_hex": "#A5B30B"},
        {"value": "4", "label": "(4)棕色", "desc": "铁锈色/黏稠", "color_class": "bg-amber-100 border-amber-200","color_hex": "#A56415"},
        {"value": "5", "label": "(5)红色", "desc": "有血丝或血块", "color_class": "bg-red-100 border-red-200","color_hex": "#EF4444"},
    ]

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid,
        "cough_options": cough_options,
        "sputum_colors": sputum_colors
    }
    
    return render(request, "web_patient/record_sputum.html", context)

def record_pain(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】疼痛情况记录页面 `/p/record/pain/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 显示当前时间作为默认测量时间。
    3. 提供疼痛情况列表（数据由后端传入）。
    4. 实现联动逻辑：选中非第一项时，展示程度单选。
    5. 提交按钮。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 获取当前时间，格式化为 YYYY/MM/DD HH:mm
    now = timezone.now()
    default_time = now.strftime("%Y/%m/%d %H:%M")

    # 疼痛部位选项
    pain_locations = [
        {"value": "0", "label": "今日无疼痛情况", "is_none": True},
        {"value": "1", "label": "术口/胸膛/肋间"},
        {"value": "2", "label": "肩峰/肩背/肩胛"},
        {"value": "3", "label": "肋骨/脊柱/骨盆/四肢"},
        {"value": "4", "label": "头痛"},
    ]

    # 疼痛程度选项
    pain_levels = [
        {
            "level": "mild",
            "label": "轻度：",
            "desc": "能做家务/正常活动，睡眠基本不受影响",
            "options": [
                {"value": "1", "label": "1分"},
                {"value": "2", "label": "2分"},
                {"value": "3", "label": "3分"},
            ]
        },
        {
            "level": "moderate",
            "label": "中度：",
            "desc": "活动或睡眠受影响，需要（或增加）止痛药",
            "options": [
                {"value": "4", "label": "4分"},
                {"value": "5", "label": "5分"},
                {"value": "6", "label": "6分"},
            ]
        },
        {
            "level": "severe",
            "label": "重度：",
            "desc": "明显疼痛或无法入眠，需要立即处理/尽快就医",
            "options": [
                {"value": "7", "label": "7分"},
                {"value": "8", "label": "8分"},
                {"value": "9", "label": "9分"},
                {"value": "10", "label": "10分"},
            ]
        },
    ]

    context = {
        "user": user,
        "default_time": default_time,
        "openid": openid,
        "pain_locations": pain_locations,
        "pain_levels": pain_levels
    }
    
    return render(request, "web_patient/record_pain.html", context)

def health_records(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】健康档案页面 `/p/health/records/`
    【功能逻辑】
    1. 展示各项健康指标的记录统计（记录次数、异常次数）。
    2. 支持空状态展示。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()

    # 模拟数据：健康指标记录
    # 实际开发中应从数据库统计
    health_stats = [
        {"type": "temperature", "title": "体温", "count": 25, "abnormal": 5, "icon": "temperature"},
        {"type": "breath", "title": "呼吸", "count": 35, "abnormal": 5, "icon": "breath"},
        {"type": "sputum", "title": "咳嗽/痰色", "count": 35, "abnormal": 5, "icon": "sputum"},
        {"type": "pain", "title": "疼痛", "count": 35, "abnormal": 5, "icon": "pain"},
        {"type": "weight", "title": "体重", "count": 35, "abnormal": 5, "icon": "weight"},
        {"type": "spo2", "title": "血氧", "count": 35, "abnormal": 5, "icon": "spo2"},
        {"type": "bp", "title": "血压心率", "count": 35, "abnormal": 5, "icon": "bp"},
        {"type": "platelet", "title": "血小板……等检验指标……以此类推", "count": 35, "abnormal": 5, "icon": "lab"},
    ]
    
    # 模拟空数据测试
    # health_stats = []

    context = {
        "user": user,
        "openid": openid,
        "health_stats": health_stats
    }

    return render(request, "web_patient/health_records.html", context)

def record_checkup(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】复查上报页面 `/p/record/checkup/`
    【功能逻辑】
    1. 接收 openid 参数标识用户。
    2. 展示本次复查日期和复查项目。
    3. 支持图片上传（前端模拟预览）。
    4. 提交按钮（前端校验每个项目至少有一张图片）。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
        
    # 模拟数据
    checkup_date = "2025-12-29"
    checkup_items = [
        {"id": 1, "name": "血常规"},
        {"id": 2, "name": "血生化"},
        {"id": 3, "name": "骨扫描"},
    ]

    context = {
        "user": user,
        "openid": openid,
        "checkup_date": checkup_date,
        "checkup_items": checkup_items
    }
    
    return render(request, "web_patient/record_checkup.html", context)
