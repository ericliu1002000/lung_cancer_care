"""web_sales 视图模块."""

from .dashboard import sales_dashboard
from .account import sales_change_password
from .patient_detail import patient_detail, update_patient_doctor
from .doctor_detail import doctor_detail

__all__ = [
    "sales_dashboard",
    "sales_change_password",
    
    "patient_detail",
    
    "update_patient_doctor",
    "doctor_detail",
]
