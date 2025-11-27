"""医生详情视图."""

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from users.decorators import check_sales
from users.services import DoctorService

logger = logging.getLogger(__name__)


@login_required
@check_sales
def doctor_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """加载医生详情局部模板。"""

    sales_profile = getattr(request.user, "sales_profile", None)
    try:
        doctor = DoctorService().get_doctor_for_sales(pk, sales_profile)
    except ValidationError as exc:
        logger.warning("医生详情访问失败：%s", exc)
        raise Http404("医生不存在或无权访问") from exc

    return render(
        request,
        "web_sales/partials/doctor_detail_card.html",
        {"doctor": doctor},
    )
