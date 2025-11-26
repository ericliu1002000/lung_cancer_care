from django.contrib.auth.forms import PasswordChangeForm


class DoctorPasswordChangeForm(PasswordChangeForm):
    """为医生端统一注入 Tailwind 样式。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        base_classes = (
            "w-full rounded-xl border border-slate-200 px-4 py-2.5 "
            "text-slate-800 focus:outline-none focus:ring-2 focus:ring-sky-200 "
            "focus:border-sky-500 bg-white"
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", base_classes)
            field.widget.attrs.setdefault("placeholder", field.label)
