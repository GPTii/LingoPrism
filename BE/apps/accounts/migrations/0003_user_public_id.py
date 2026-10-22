import secrets

from django.db import migrations, models


def fill(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    used = set()
    for user in User.objects.filter(public_id__isnull=True).only("id"):
        while True:
            code = str(secrets.randbelow(90_000_000) + 10_000_000)
            if code not in used:
                break
        used.add(code)
        User.objects.filter(pk=user.pk).update(public_id=code)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_user_avatar_preset")]

    operations = [
        migrations.AddField(model_name="user", name="public_id", field=models.CharField(max_length=8, null=True, editable=False)),
        migrations.RunPython(fill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user", name="public_id",
            field=models.CharField(editable=False, help_text="ID 8 số để bạn bè tìm nhau", max_length=8, unique=True),
        ),
    ]
