"""users admin package imports."""

import types

from django.contrib import admin

from .sales import SalesProfileAdmin
from .doctors import DoctorProfileAdmin, DoctorStudioAdmin
from .assistants import AssistantProfileAdmin
from .patients import PatientProfileAdmin
from .platform import PlatformAdminUserAdmin

MODEL_ORDER = [
    "平台管理员",
    "医生档案",
    "医生助理",
    "医生工作室",
    "患者列表",
    "销售档案",
]


def _sorted_app_list(self, request):
    app_dict = self._build_app_dict(request)
    app_list = []
    users_app = app_dict.pop("users", None)
    for label, app in app_dict.items():
        if app["app_label"] == "users" and users_app is None:
            users_app = app
        else:
            app_list.append(app)
    app_list.sort(key=lambda x: x["name"])
    if users_app:
        users_app["name"] = "用户模块"
        users_app["models"].sort(
            key=lambda m: MODEL_ORDER.index(m["name"]) if m["name"] in MODEL_ORDER else len(MODEL_ORDER)
        )
        app_list.insert(0, users_app)
    return app_list


admin.site.get_app_list = types.MethodType(_sorted_app_list, admin.site)

__all__ = [
    "SalesProfileAdmin",
    "DoctorProfileAdmin",
    "DoctorStudioAdmin",
    "AssistantProfileAdmin",
    "PatientProfileAdmin",
    "PlatformAdminUserAdmin",
]
