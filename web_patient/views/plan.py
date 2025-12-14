from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from users.models import CustomUser

def management_plan(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】管理计划页面 `/p/plan/`
    【功能逻辑】
    1. 展示每日固定计划（用药、体温、血氧等）。
    2. 展示动态疗程计划（随访、复查等）。
    3. 支持接收 openid 参数，用于标识当前用户（虽然实际业务中应从 request.user 获取，此处按需求兼容 URL 传参）。
    """
    
    # 获取 openid 参数
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()
    
    # 模拟数据：每日固定计划
    daily_tasks = [
        {"title": "按时用药", "status": "completed", "status_text": "已完成", "icon": "medication"},
        {"title": "测量体温", "status": "pending", "status_text": "未完成", "icon": "thermometer"},
        {"title": "测量血氧", "status": "pending", "status_text": "未完成", "icon": "spo2"},
        {"title": "测量血压/心率", "status": "pending", "status_text": "未完成", "icon": "bp"},
        {"title": "测量体重", "status": "pending", "status_text": "未完成", "icon": "weight"},
    ]

    # 模拟数据：疗程计划
    treatment_courses = [
        {
            "name": "第一疗程",
            "items": [
                {"title": "第1次随访", "date": "2025-11-01", "status": "completed", "status_text": "已完成", "type": "followup"},
                {"title": "第1次复查", "date": "2025-11-01", "status": "completed", "status_text": "已完成", "type": "checkup"},
                {"title": "第2次随访", "date": "2025-12-21", "status": "pending", "status_text": "未开始", "type": "followup"},
                {"title": "第2次复查", "date": "2025-12-22", "status": "pending", "status_text": "未开始", "type": "checkup"},
            ]
        },
        {
            "name": "第二疗程",
            "items": [
                {"title": "第一次随访", "date": "2025-11-01", "status": "pending", "status_text": "未开始", "type": "followup"},
                {"title": "第一次复查", "date": "2025-11-01", "status": "pending", "status_text": "未开始", "type": "checkup"},
            ]
        },
        {
            "name": "第三疗程",
            "items": [
                {"title": "第一次随访", "date": "2025-11-01", "status": "pending", "status_text": "未开始", "type": "followup"},
                {"title": "第一次复查", "date": "2025-11-01", "status": "pending", "status_text": "未开始", "type": "checkup"},
            ]
        }
    ]

    context = {
        "user": user,
        "daily_tasks": daily_tasks,
        "treatment_courses": treatment_courses,
        "openid": openid
    }
    
    return render(request, "web_patient/management_plan.html", context)

def my_medication(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】我的用药页面 `/p/medication/`
    【功能逻辑】
    1. 展示当前用药列表。
    2. 展示历史用药列表。
    3. 支持空状态展示。
    """
    
    openid = request.GET.get('openid')
    user = None
    if openid:
        user = CustomUser.objects.filter(wx_openid=openid).first()

    # 模拟数据：当前用药（第三疗程）
    current_medications = [
        {
            "course_name": "第三疗程",
            "start_date": "2025-11-01",
            "end_date": None, # 当前正在进行，无结束日期
            "drugs": [
                {"name": "培美曲塞", "frequency": "每21天一个周期，第1天", "dosage": "1000mg", "usage": "静脉注射"},
                {"name": "卡铂", "frequency": "每21天一个周期，第1天", "dosage": "300mg", "usage": "静脉注射"},
                {"name": "吉非替尼", "frequency": "每日1次", "dosage": "250mg", "usage": "口服"},
            ]
        }
    ]

    # 模拟数据：历史用药（第二、第一疗程）
    history_medications = [
        {
            "course_name": "第二疗程",
            "start_date": "2025-06-01",
            "end_date": "2025-11-01",
            "drugs": [
                {"name": "培美曲塞", "frequency": "每21天一个周期，第1天", "dosage": "1000mg", "usage": "静脉注射"},
                {"name": "卡铂", "frequency": "每21天一个周期，第1天", "dosage": "300mg", "usage": "静脉注射"},
                {"name": "吉非替尼", "frequency": "每日1次", "dosage": "250mg", "usage": "口服"},
            ]
        },
        {
            "course_name": "第一疗程",
            "start_date": "2025-01-01",
            "end_date": "2025-06-01",
            "drugs": [
                {"name": "培美曲塞", "frequency": "每21天一个周期，第1天", "dosage": "1000mg", "usage": "静脉注射"},
                {"name": "卡铂", "frequency": "每21天一个周期，第1天", "dosage": "300mg", "usage": "静脉注射"},
                {"name": "吉非替尼", "frequency": "每日1次", "dosage": "250mg", "usage": "口服"},
            ]
        }
    ]

    context = {
        "user": user,
        "openid": openid,
        "current_medications": current_medications,
        "history_medications": history_medications
    }

    return render(request, "web_patient/my_medication.html", context)
