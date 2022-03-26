# Generated by Django 3.2.9 on 2022-03-26 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0017_item_connected_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='status',
            field=models.IntegerField(choices=[(-1, 'Removed from Inventory'), (1, 'Not Yet Received'), (2, 'Awaiting Removal'), (3, 'Stored'), (10, 'Ready'), (11, 'In Use')], default=0, help_text='The status of this item', verbose_name='status'),
        ),
    ]
