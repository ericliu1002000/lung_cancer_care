import logging
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from users.decorators import check_doctor_or_assistant
from web_doctor.views.workspace import _get_workspace_identities, _get_workspace_patients, get_user_display_name

logger = logging.getLogger(__name__)

def getTodoList(request, page=1, size=10):
    """
    获取待办事项列表（模拟数据），支持分页和筛选
    """
    # 获取筛选参数
    status_filter = request.GET.get('status', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 生成模拟数据
    # 扩展数据字段以匹配需求：事件、类型、等级、时间、处理时间、处理人、状态
    mock_data = []
    statuses = ['pending', 'pending', 'escalate', 'completed', 'completed']
    types = ['行为异常', '数据异常', '新增档案', '问卷异常']
    levels = ['1级', '2级', '3级']
    handlers = ['李白', '杜甫', '白居易', '']
    
    # 基础时间
    base_time = datetime.now()

    for i in range(1, 56):  # 生成55条数据以测试分页
        # 模拟不同状态和数据
        status = statuses[i % 5]
        evt_type = types[i % 4]
        level = levels[i % 3]
        handler = handlers[i % 4] if status == 'completed' else ''
        
        # 模拟时间差异
        event_time = base_time - timedelta(days=i, hours=i%12)
        handle_time = (event_time + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S') if status == 'completed' else ''
        
        item = {
            'id': i,
            'event_title': f'模拟事件_{i}',
            'patient_name': f'患者_{i}',
            'event_type': evt_type,
            'event_level': level,
            'event_time': event_time.strftime('%Y-%m-%d %H:%M:%S'),
            'handle_time': handle_time,
            'handler': handler,
            'status': status,
            'event_content': f'这是关于患者_{i}的{evt_type}详情说明，需要医生关注处理。',
            'handle_content': f'已由{handler}处理完成，情况稳定。' if status == 'completed' else '',
            'status_display': {
                'pending': '待跟进', 
                'escalate': '升级主任', 
                'completed': '已完成'
            }.get(status, '未知')
        }
        
        # 简单的内存过滤逻辑
        if status_filter != 'all' and status != status_filter:
            continue
            
        if start_date and item['event_time'] < start_date:
            continue
        if end_date and item['event_time'] > end_date + ' 23:59:59':
            continue
            
        mock_data.append(item)

    # 分页处理
    paginator = Paginator(mock_data, size)
    try:
        todo_page = paginator.page(page)
    except PageNotAnInteger:
        todo_page = paginator.page(1)
    except EmptyPage:
        todo_page = paginator.page(paginator.num_pages)

    return todo_page

@login_required
@check_doctor_or_assistant
def doctor_workspace(request: HttpRequest) -> HttpResponse:
    """
    医生工作台主视图（带待办事项功能）：
    - 左侧展示该医生名下患者列表（可搜索）
    - 右侧展示患者待办事项
    """
    # TODO 待联调首页-患者待办列表：列表项包含事项分类、事项名称、事项报警内容、事项处理状态、事项创建时间
    # 获取基础上下文以保证页面布局正常（如左侧患者列表）
    doctor_profile, assistant_profile = _get_workspace_identities(request.user)
    patients = _get_workspace_patients(request.user, request.GET.get("q"))
    display_name = get_user_display_name(request.user)

    # 使用新的 getTodoList 获取数据 (取第一页前5条作为首页概览)
    # 注意：首页概览可能只需要少量数据，这里简化处理，直接调用
    todo_page = getTodoList(request, page=1, size=5)

    # 为了兼容旧的模板变量名 todo_list，这里做个转换
    # 注意：todo_page 是 Page 对象，也可以迭代
    
    return render(
        request,
        "web_doctor/index.html",
        {
            "doctor": doctor_profile,
            "assistant": assistant_profile,
            "workspace_display_name": display_name,
            "patients": patients,
            "todo_list": todo_page.object_list,  # 首页仅展示列表数据
        },
    )

@login_required
@check_doctor_or_assistant
def doctor_todo_list_page(request: HttpRequest) -> HttpResponse:
    """
    待办列表全屏页面
    """
    # TODO 待联调患者待办列表接口
    # TODO 1、分页查询、筛选条件包含事件状态（待跟进、升级主任、已完成）、开始日期、结束日期
    # TODO 2、列表项内容包含：事件名称、事件类型、事件等级、事件时间、处理时间、处理人、当前状态
    doctor_profile, assistant_profile = _get_workspace_identities(request.user)
    display_name = get_user_display_name(request.user)
    
    page = request.GET.get('page', 1)
    size = request.GET.get('size', 10)
    
    todo_page = getTodoList(request, page=page, size=size)
    
    context = {
        "doctor": doctor_profile,
        "assistant": assistant_profile,
        "workspace_display_name": display_name,
        "todo_page": todo_page,
        # 保留筛选参数回显
        "current_status": request.GET.get('status', 'all'),
        "start_date": request.GET.get('start_date', ''),
        "end_date": request.GET.get('end_date', ''),
    }
    
    # HTMX 请求只返回列表部分
    if request.headers.get('HX-Request'):
        return render(request, "web_doctor/partials/todo_list/todo_list_table.html", context)
        
    return render(request, "web_doctor/partials/todo_list/todo_list.html", context)
