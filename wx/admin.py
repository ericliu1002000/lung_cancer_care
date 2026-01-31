from django.contrib import admin
from .models import MessageTemplate, SendMessageLog

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_active", "updated_at")
    search_fields = ("code", "title", "content")
    readonly_fields = ("code",) # 建议创建后 code 不许改，防止代码里找不到
    
    def get_readonly_fields(self, request, obj=None):
        if obj: # 编辑模式下 code 只读
            return self.readonly_fields
        return ()


@admin.register(SendMessageLog)
class SendMessageLogAdmin(admin.ModelAdmin):
    list_display = ("scene", "channel", "biz_date", "patient", "user", "is_success", "created_at")
    list_filter = ("scene", "channel", "is_success", "biz_date")
    search_fields = ("openid", "content")
    readonly_fields = ("scene", "channel", "biz_date", "patient", "user", "openid", "content", "payload", "is_success", "error_message", "created_at", "updated_at")
