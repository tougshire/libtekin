# Generated by Django 3.2.9 on 2022-03-01 19:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0016_rename_is_major_itemnote_is_current'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='connected_to',
            field=models.ForeignKey(blank=True, help_text='For peripherals and components, the device to which this item is connected. For example, if this item is a monitor, choose its computer.  If this is the computer, do not enter the monitor here', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.item'),
        ),
    ]
