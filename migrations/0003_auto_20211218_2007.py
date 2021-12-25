# Generated by Django 3.2.9 on 2021-12-19 01:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0002_auto_20211218_1616'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mmodel',
            name='categories',
        ),
        migrations.AddField(
            model_name='mmodel',
            name='category',
            field=models.ForeignKey(blank=True, help_text='The category, such as Laptop or Phone, to which this item belongs', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.mmodelcategory', verbose_name='category'),
        ),
    ]