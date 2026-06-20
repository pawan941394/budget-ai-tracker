from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("budget_users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="BudgetTransactionBucket",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transactions", models.JSONField(default=list)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="transaction_bucket", to="budget_users.budgetuser")),
            ],
        ),
    ]
