from django.contrib.auth.forms import PasswordChangeForm


class SalesPasswordChangeForm(PasswordChangeForm):
    """销售端密码修改表单，注入 Tailwind 样式。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = (
            "w-full rounded-xl border border-slate-200 px-4 py-2.5 "
            "text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-200 "
            "focus:border-blue-500 bg-white"
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", base_classes)
            field.widget.attrs.setdefault("placeholder", field.label)
