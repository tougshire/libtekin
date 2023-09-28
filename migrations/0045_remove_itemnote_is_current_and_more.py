# Generated by Django 4.2.4 on 2023-09-27 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0044_alter_itemnote_is_current'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemnote',
            name='is_current',
        ),
        migrations.AddField(
            model_name='itemnotelevel',
            name='view_by_default',
            field=models.IntegerField(default=0, help_text='If notes of this level should show up by default in an item detail view', verbose_name='view by default'),
        ),
    ]