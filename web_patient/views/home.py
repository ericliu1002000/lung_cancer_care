import logging
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpRequest, HttpResponse
from users.models import CustomUser
from users import choices
from wx.services.oauth import generate_menu_auth_url

logger = logging.getLogger(__name__)

def patient_home(request):
    """
    【页面说明】患者端首页 `/p/home/`
    【模板】`web_patient/patient_home.html`，根据本人或家属身份展示功能入口与卡片。
    """
    
    # 获取 onboarding 页面的 URL，用于未登录时的跳转
    onboarding_url = reverse("web_patient:onboarding")

    # 模拟获取用户信息
    openid = "oR9yO2JHqO_YZxc2PdPAMCk7qhVU"
  
    patient = {
       "is_member": "1",
       "membership_expire_date": "2026-01-01 00:00:00",
       "name": "患者",
       "age": "80",
       "openId": "oR9yO2JHqO_YZxc2PdPAMCk7qhVU"
    }
    # 模拟每日计划数据
    daily_plans = [ {
                "type": "medication",
                "title": "用药提醒",
                "subtitle": "您今天还未服药",
                "status": "pending",
                "action_text": "去服药",
                "icon_class": "bg-blue-100 text-blue-600", 
            },{
                "type": "step",
                "title": "今日步数",
                "subtitle": "您今天还未记录",
                "status": "pending",
                "action_text": "去填写",
                "icon_class": "bg-blue-100 text-blue-600", 
            },
        {
            "type": "temperature",
            "title": "测量体温",
            "subtitle": "请记录今日体温",
            "status": "pending",
            "action_text": "去填写",
                "icon_class": "bg-blue-100 text-blue-600",
        },
            {
            "type": "bp_hr",
            "title": "血压心率",
            "subtitle": "请记录今日血压心率情况",
            "status": "pending",
            "action_text": "去填写",
                "icon_class": "bg-blue-100 text-blue-600",
        },
        {
            "type": "spo2",
            "title": "血氧饱和度",
            "subtitle": "请记录今日血氧饱和度",
            "status": "pending",
            "action_text": "去填写",
                "icon_class": "bg-blue-100 text-blue-600",
        },
            {
            "type": "weight",
            "title": "体重记录",
            "subtitle": "请记录今日体重",
            "status": "pending",
            "action_text": "去填写",
                "icon_class": "bg-blue-100 text-blue-600",
        },
            {
            "type": "breath",
            "title": "呼吸情况",
            "subtitle": "请自测呼吸情况",
            "status": "pending",
            "action_text": "去自测",
                "icon_class": "bg-blue-100 text-blue-600",
        },
        {
            "type": "sputum",
            "title": "咳嗽与痰色情况自测",
            "subtitle": "请自测咳嗽与痰色",
            "status": "pending",
            "action_text": "去自测",
                "icon_class": "bg-blue-100 text-blue-600",
        },
        {
            "type": "pain",
            "title": "疼痛情况记录",
            "subtitle": "请记录今日疼痛情况",
            "status": "pending",
            "action_text": "去记录",
                "icon_class": "bg-blue-100 text-blue-600",
        },
        {
            "type": "followup",
            "title": "第1次随访",
            "subtitle": "请及时完成您的第1次随访",
            "status": "pending",
            "action_text": "去完成",
                "icon_class": "bg-blue-100 text-blue-600",
        },
            {
            "type": "checkup",
            "title": "第1次复查",
            "subtitle": "请及时完成您的第1次复查",
            "status": "pending",
            "action_text": "去完成",
                "icon_class": "bg-blue-100 text-blue-600",
        },
    ]

    # 处理体温录入返回的逻辑
    # 如果 URL 中携带了 temp_val 参数，说明刚刚完成了体温录入
    # 模拟重新获取计划列表数据
    temp_val = request.GET.get('temp_val')
    bp_val = request.GET.get('bp_val')
    
    if temp_val:
        # 这里模拟后端接口逻辑：
        # 1. 接收到前端传来的 temp_val (提交成功标识)
        # 2. 重新查询数据库（这里直接修改模拟数据）
        # 3. 返回更新后的数据
        for plan in daily_plans:
            if plan['type'] == 'temperature':
                plan['status'] = 'completed'
                plan['subtitle'] = f"今日已记录：{temp_val}°C"
                plan['action_text'] = f"已记录今日体温-{temp_val}°C"
                
    # 处理步数录入返回的逻辑
    # 如果 URL 中携带了 temp_val 参数，说明刚刚完成了体温录入
    # 模拟重新获取计划列表数据
    step_val = request.GET.get('step_val')
    if step_val:
        # 这里模拟后端接口逻辑：
        # 1. 接收到前端传来的 temp_val (提交成功标识)
        # 2. 重新查询数据库（这里直接修改模拟数据）
        # 3. 返回更新后的数据
        for plan in daily_plans:
            if plan['type'] == 'step':
                plan['status'] = 'completed'
                plan['subtitle'] = f"今日已记录：{step_val}步"
                plan['action_text'] = f"已记录今日体温-{temp_val}°C"
                
    if bp_val:
        # bp_val 格式假设为 "120/80,75" (收缩压/舒张压,心率)
        try:
            bp_str, hr_str = bp_val.split(',')
            for plan in daily_plans:
                if plan['type'] == 'bp_hr':
                    plan['status'] = 'completed'
                    plan['subtitle'] = f"今日已记录：血压{bp_str}mmHg，心率{hr_str}次/分"
                    plan['action_text'] = f"已记录今日血压心率"
        except ValueError:
            pass
            
    # 处理血氧录入返回逻辑
    spo2_val = request.GET.get('spo2_val')
    if spo2_val:
        for plan in daily_plans:
            if plan['type'] == 'spo2':
                plan['status'] = 'completed'
                plan['subtitle'] = f"今日已记录：{spo2_val}%"
                plan['action_text'] = f"已记录今日血氧"

    # 处理体重录入返回逻辑
    weight_val = request.GET.get('weight_val')
    if weight_val:
        for plan in daily_plans:
            if plan['type'] == 'weight':
                plan['status'] = 'completed'
                plan['subtitle'] = f"今日已记录：{weight_val}KG"
                plan['action_text'] = f"已记录今日体重"

    # 处理呼吸情况自测返回逻辑
    breath_val = request.GET.get('breath_val')
    if breath_val:
        for plan in daily_plans:
            if plan['type'] == 'breath':
                plan['status'] = 'completed'
                plan['subtitle'] = "今日已记录呼吸情况"
                plan['action_text'] = "已记录今日呼吸情况"

    # 处理咳嗽与痰色自测返回逻辑
    sputum_val = request.GET.get('sputum_val')
    if sputum_val:
        for plan in daily_plans:
            if plan['type'] == 'sputum':
                plan['status'] = 'completed'
                plan['subtitle'] = "今日已记录咳嗽与痰色情况"
                plan['action_text'] = "已记录"

    # 处理疼痛记录返回逻辑
    pain_val = request.GET.get('pain_val')
    if pain_val:
        for plan in daily_plans:
            if plan['type'] == 'pain':
                plan['status'] = 'completed'
                plan['subtitle'] = "今日已记录疼痛情况"
                plan['action_text'] = "已记录"
                
    # 处理复查上报返回逻辑
    checkup_completed = request.GET.get('checkup_completed')
    if checkup_completed:
        for plan in daily_plans:
            if plan['type'] == 'checkup':
                plan['status'] = 'completed'
                plan['subtitle'] = "本次复查已上报"
                plan['action_text'] = "已完成"

    # 处理用药提醒返回逻辑
    medication_taken = request.GET.get('medication_taken')
    if medication_taken:
        for plan in daily_plans:
            if plan['type'] == 'medication':
                plan['status'] = 'completed'
                plan['subtitle'] = "您今天已服药"
                plan['action_text'] = "已服药"

    context = {
        "patient": patient, # 传递用户信息
        "service_days": 135,
        "is_member": True, # For "Member open" text
        "is_family": False,
        "onboarding_url": onboarding_url,
        "daily_plans": daily_plans,
        "buy_url": generate_menu_auth_url("market:product_buy")

    }
    return render(request, "web_patient/patient_home.html", context)



# import logging
# from django.shortcuts import render, redirect
# from django.urls import reverse
# from django.http import HttpRequest, HttpResponse
# from users.models import CustomUser
# from users import choices
# from wx.services.oauth import generate_menu_auth_url
# from users.decorators import auto_wechat_login, check_patient

# logger = logging.getLogger(__name__)

# # @auto_wechat_login
# @check_patient
# def patient_home(request: HttpRequest) -> HttpResponse:
#     """
#     【页面说明】患者端首页 `/p/home/`
#     【模板】`web_patient/patient_home.html`，根据本人或家属身份展示功能入口与卡片。
#     """
    
#     # 获取 onboarding 页面的 URL，用于未登录时的跳转
#     onboarding_url = reverse("web_patient:onboarding")

#     # 模拟获取用户信息
#     openid = "oR9yO2JHqO_YZxc2PdPAMCk7qhVU"
#     user = CustomUser.objects.filter(wx_openid=openid).first()
    
#     if not user:
#         user = CustomUser.objects.create(
#             wx_openid=openid,
#             wx_nickname="微信用户",
#             user_type=choices.UserType.PATIENT,
#             is_active=True,
#         )
#         logger.info(f"Created new user with openid: {openid}")
    
#     logger.info(f"aaaa: {user.__dict__}")

#     # ========== 新增：任务类型与URL名称的映射（核心改造） ==========
#     # 键：plan.type，值：URL名称（需与urls.py中定义的name一致）
#     task_url_mapping = {
#         "temperature": "web_patient:record_temperature",
#         "bp_hr": "web_patient:record_bp",
#         "spo2": "web_patient:record_spo2",
#         "weight": "web_patient:record_weight",
#         "breath": "web_patient:record_breath",
#         "sputum": "web_patient:record_sputum",
#         "pain": "web_patient:record_pain",
#         "followup": "web_patient:record_temperature",  # 替换为实际的随访URL名称
#         "checkup": "web_patient:record_temperature",    # 替换为实际的复查URL名称
#     }

#     # 模拟每日计划数据
#     daily_plans = [
#         {
#             "type": "temperature",
#             "title": "测量体温",
#             "subtitle": "请记录今日体温",
#             "status": "pending",
#             "action_text": "去填写",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "bp_hr",
#             "title": "血压心率",
#             "subtitle": "请记录今日血压心率情况",
#             "status": "pending",
#             "action_text": "去填写",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "spo2",
#             "title": "血氧饱和度",
#             "subtitle": "请记录今日血氧饱和度",
#             "status": "pending",
#             "action_text": "去填写",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "weight",
#             "title": "体重记录",
#             "subtitle": "请记录今日体重",
#             "status": "pending",
#             "action_text": "去填写",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "breath",
#             "title": "呼吸情况",
#             "subtitle": "请自测呼吸情况",
#             "status": "pending",
#             "action_text": "去自测",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "sputum",
#             "title": "咳嗽与痰色情况自测",
#             "subtitle": "请自测咳嗽与痰色",
#             "status": "pending",
#             "action_text": "去自测",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "pain",
#             "title": "疼痛情况记录",
#             "subtitle": "请记录今日疼痛情况",
#             "status": "pending",
#             "action_text": "去记录",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "followup",
#             "title": "第1次随访",
#             "subtitle": "请及时完成您的第1次随访",
#             "status": "pending",
#             "action_text": "去完成",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#         {
#             "type": "checkup",
#             "title": "第1次复查",
#             "subtitle": "请及时完成您的第1次复查",
#             "status": "pending",
#             "action_text": "去完成",
#             "icon_class": "bg-blue-100 text-blue-600",
#         },
#     ]

#     # ========== 新增：为每个计划生成授权后的完整URL ==========
#     for plan in daily_plans:
#         task_type = plan["type"]
#         # 生成带微信授权的基础URL
#         base_url = generate_menu_auth_url(task_url_mapping.get(task_type, "#"))
#         # 拼接openid参数（确保目标页面能获取用户信息）
#         # plan["auth_url"] = f"{base_url}?openid={user.wx_openid}" if user else base_url
#         plan["auth_url"] = f"{base_url}"

#     # 处理各类录入返回的逻辑（保持原有代码不变）
#     temp_val = request.GET.get('temp_val')
#     bp_val = request.GET.get('bp_val')
    
#     if temp_val:
#         for plan in daily_plans:
#             if plan['type'] == 'temperature':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = f"今日已记录：{temp_val}°C"
#                 plan['action_text'] = f"已记录今日体温-{temp_val}°C"
                
#     if bp_val:
#         try:
#             bp_str, hr_str = bp_val.split(',')
#             for plan in daily_plans:
#                 if plan['type'] == 'bp_hr':
#                     plan['status'] = 'completed'
#                     plan['subtitle'] = f"今日已记录：血压{bp_str}mmHg，心率{hr_str}次/分"
#                     plan['action_text'] = f"已记录今日血压心率"
#         except ValueError:
#             pass
            
#     spo2_val = request.GET.get('spo2_val')
#     if spo2_val:
#         for plan in daily_plans:
#             if plan['type'] == 'spo2':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = f"今日已记录：{spo2_val}%"
#                 plan['action_text'] = f"已记录今日血氧"

#     weight_val = request.GET.get('weight_val')
#     if weight_val:
#         for plan in daily_plans:
#             if plan['type'] == 'weight':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = f"今日已记录：{weight_val}KG"
#                 plan['action_text'] = f"已记录今日体重"

#     breath_val = request.GET.get('breath_val')
#     if breath_val:
#         for plan in daily_plans:
#             if plan['type'] == 'breath':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = "今日已记录呼吸情况"
#                 plan['action_text'] = "已记录今日呼吸情况"

#     sputum_val = request.GET.get('sputum_val')
#     if sputum_val:
#         for plan in daily_plans:
#             if plan['type'] == 'sputum':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = "今日已记录咳嗽与痰色情况"
#                 plan['action_text'] = "已记录"

#     pain_val = request.GET.get('pain_val')
#     if pain_val:
#         for plan in daily_plans:
#             if plan['type'] == 'pain':
#                 plan['status'] = 'completed'
#                 plan['subtitle'] = "今日已记录疼痛情况"
#                 plan['action_text'] = "已记录"

#     context = {
#         "user": user,
#         "service_days": 135,
#         "is_member": True,
#         "is_family": False,
#         "onboarding_url": onboarding_url,
#         "daily_plans": daily_plans,  # 已包含auth_url字段
#         "buy_url": generate_menu_auth_url("market:product_buy")
#     }
#     return render(request, "web_patient/patient_home.html", context)