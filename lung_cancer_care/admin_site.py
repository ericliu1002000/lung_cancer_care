"""肺部康复管理平台的自定义后台站点配置。"""

from django.conf import settings
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class LungCancerAdminSite(AdminSite):
    site_header = "肺部康复管理系统后台"
    site_title = "肺部康复管理系统"
    index_title = "后台管理首页"

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)
        ordered_list = []
        preferred_order = getattr(settings, "ADMIN_APP_ORDER", [])

        for app_label in preferred_order:
            app_config = app_dict.pop(app_label, None)
            if app_config:
                ordered_list.append(app_config)

        # 其余应用按名称字母序追加，保持体验一致。
        ordered_list.extend(sorted(app_dict.values(), key=lambda app: app["name"].lower()))
        return ordered_list


class LungCancerAdminConfig(AdminConfig):
    default_site = "lung_cancer_care.admin_site.LungCancerAdminSite"
