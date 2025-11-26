"""销售端账号相关视图。"""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from users.decorators import check_sales

from ..forms import SalesPasswordChangeForm


@login_required
@check_sales
def sales_change_password(request: HttpRequest) -> HttpResponse:
    """销售端修改密码。"""

    if request.method == "POST":
        form = SalesPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "密码修改成功")
            return redirect("web_sales:sales_dashboard")
        messages.error(request, "请检查输入是否正确")
    else:
        form = SalesPasswordChangeForm(request.user)

    return render(
        request,
        "web_sales/change_password.html",
        {
            "form": form,
        },
    )
