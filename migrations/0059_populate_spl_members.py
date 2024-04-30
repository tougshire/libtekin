import datetime
from django.db import migrations


def forwards_func(apps, schema_editor):
    Item = apps.get_model("libtekin", "Item")
    ItemAssignee = apps.get_model("libtekin", "ItemAssignee")
    ItemBorrower = apps.get_model("libtekin", "ItemBorrower")

    Member = apps.get_model("spl_members", "Member")
    db_alias = schema_editor.connection.alias

    for item in Item.objects.using(db_alias).all():
        if item.assignee is not None:
            member, created = Member.objects.get_or_create(
                name_full=item.assignee.full_name
            )
            item.spl_member_assignee = member
            item.save()
        if item.borrower is not None:
            member, created = Member.objects.get_or_create(
                name_full=item.borrower.full_name
            )
            item.spl_member_borrower = member
            item.save()

        for item_assignee in ItemAssignee.objects.filter(item=item):
            if item_assignee.entity is not None:
                member, created = Member.objects.get_or_create(
                    name_full=item_assignee.entity.full_name
                )
                item_assignee.spl_member_assignee = member
                item_assignee.save()
        for item_borrower in ItemAssignee.objects.filter(item=item):
            if item_borrower.entity is not None:
                member, created = Member.objects.get_or_create(
                    name_full=item_borrower.entity.full_name
                )
                item_borrower.spl_member_borrower = member
                item_borrower.save()


class Migration(migrations.Migration):
    dependencies = [
        ("libtekin", "0058_item_spl_member_assignee_item_spl_member_borrower_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
