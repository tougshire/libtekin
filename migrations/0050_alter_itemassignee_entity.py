# Generated by Django 4.2.4 on 2023-10-07 16:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0049_populate_itemborrower_itemprimaryholder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='itemassignee',
            name='entity',
            field=models.ForeignKey(blank=True, help_text='The person or group to whom the item was assigned', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.entity'),
        ),
    ]
