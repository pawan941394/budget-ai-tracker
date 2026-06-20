from django.contrib import admin

from budget_llmapikey.models import Llmapikey


@admin.register(Llmapikey)
class LlmapikeyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "provider", "is_active", "created_at")
    search_fields = ("user__phone_number", "provider")
