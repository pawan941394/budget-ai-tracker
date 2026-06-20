from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("budget_llmapikey", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="llmapikey",
            name="user",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="llm_api_key", to="budget_users.budgetuser"),
        ),
    ]
