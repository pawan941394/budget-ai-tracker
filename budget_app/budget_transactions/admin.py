from django.contrib import admin

from budget_transactions.models import BudgetTransactionBucket


@admin.register(BudgetTransactionBucket)
class BudgetTransactionBucketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "updated_at", "created_at")
    search_fields = ("user__phone_number",)
