# Create your views here.
"""web_doctor 应用视图：登录、医生/销售工作台。"""

from django.contrib import messages
from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from users.decorators import check_doctor_or_assistant
from users.decorators import check_sales
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from users import choices
from users.services.auth import AuthService

@check_sales
def sales_dashboard(request: HttpRequest) -> HttpResponse:
    """销售端 Dashboard 占位页。"""

    return render(request, "web_sales/sales_index.html")
