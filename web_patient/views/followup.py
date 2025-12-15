from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from users.decorators import auto_wechat_login, check_patient

@auto_wechat_login
@check_patient
def daily_survey(request: HttpRequest) -> HttpResponse:
    """
    【页面说明】今日随访问卷 `/p/followup/daily/`
    """
    if request.method == "POST":
        # Handle form submission here
        # For now, we just accept it and maybe redirect or return success
        # In a real app, we would save the data to models
        pass

    return render(request, "web_patient/followup/daily_survey.html", {})
