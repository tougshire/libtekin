# Generated by Django 3.2.9 on 2022-05-14 21:38

from django.db import migrations, models
import django.db.models.deletion

def forwards_func(apps, schema_editor):
    Status = apps.get_model("libtekin", "Status")
    Item = apps.get_model("libtekin", "Item")
    db_alias = schema_editor.connection.alias
    for item in Item.objects.using(db_alias).all():
        status, created = Status.objects.get_or_create(
            name = item.get_status_display()
        )
        status.save()
        item.status_new = status
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0021_auto_20220514_1738'),
    ]

    operations = [
        migrations.RunPython(forwards_func)
    ]
