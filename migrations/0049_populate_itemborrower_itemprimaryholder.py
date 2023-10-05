import datetime
from django.db import migrations


def forwards_func(apps, schema_editor):
    Item = apps.get_model("libtekin", "Item")
    ItemBorrower = apps.get_model("libtekin", "ItemBorrower")
    ItemAssignee = apps.get_model("libtekin", "ItemAssignee")
    Entity = apps.get_model("libtekin", "Entity")

    ItemAssignee = apps.get_model("libtekin", "ItemAssignee")
    db_alias = schema_editor.connection.alias

    for item in Item.objects.using(db_alias).all():
        if item.borrower is not None:
            ItemBorrower.objects.using(db_alias).create(
                item=item,
                entity=Entity.objects.using(db_alias).get(pk=item.borrower.id),
                when=datetime.date.today(),
            ),
        if item.assignee is not None:
            ItemAssignee.objects.using(db_alias).create(
                item=item,
                entity=Entity.objects.using(db_alias).get(pk=item.assignee.id),
                when=datetime.date.today(),
            )


def reverse_func(apps, schema_editor):
    Item = apps.get_model("libtekin", "Item")
    ItemBorrower = apps.get_model("libtekin", "ItemBorrower")
    ItemAssignee = apps.get_model("libtekin", "ItemAssignee")
    Entity = apps.get_model("libtekin", "Entity")

    ItemAssignee = apps.get_model("libtekin", "ItemAssignee")
    db_alias = schema_editor.connection.alias

    ItemBorrower.objects.using(db_alias).all().delete()
    ItemAssignee.objects.using(db_alias).all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("libtekin", "0048_itemassignee_itemborrower"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
