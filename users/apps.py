from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    【业务说明】Django App 配置，集中用户域模型与信号。
    【用法】自动被 INSTALLED_APPS 引入，无需手动调用。
    【使用示例】settings INSTALLED_APPS 中列出 'users' 即可。
    【参数】继承 AppConfig 默认参数。
    【返回值】配置对象。
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
