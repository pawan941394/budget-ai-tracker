from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from budget_users.models import BudgetUser


@admin.register(BudgetUser)
class BudgetUserAdmin(UserAdmin):
    model = BudgetUser
    list_display = ("id", "phone_number", "is_staff", "is_active")
    search_fields = ("phone_number",)
    ordering = ("id",)
    readonly_fields = ("date_joined",)
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone_number", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )
