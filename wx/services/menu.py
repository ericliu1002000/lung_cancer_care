from .client import wechat_client
from .oauth import generate_menu_auth_url

def create_menu():
    wechat_client.menu.delete()
    home_url = generate_menu_auth_url("web_patient:patient_home")
    dashboard_url = generate_menu_auth_url("web_patient:patient_dashboard")
    MENU = {
        "button": [
            {
                "type": "view",
                "name": "管理计划",  # 按钮显示名称，自定义
                "url": home_url,
                },
            {
                "type": "view",
                "name": "个人中心",  # 按钮显示名称，自定义
                "url": dashboard_url,
                }
            ]
        }
    wechat_client.menu.create(MENU)
