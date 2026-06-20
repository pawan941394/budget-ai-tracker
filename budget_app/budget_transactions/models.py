from django.conf import settings
from django.db import models


class BudgetTransactionBucket(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transaction_bucket")
    transactions = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transactions for user {self.user_id}"
