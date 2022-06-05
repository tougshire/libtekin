# Generated by Django 3.2.9 on 2022-05-14 21:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0020_alter_item_connected_to'),
    ]

    operations = [
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The status of the load', max_length=50)),
                ('list_order', models.IntegerField(default=1000, help_text='The order that this status should display in a list of statuses', verbose_name='rank')),
                ('is_active', models.BooleanField(default=False, help_text='If this status is for an active project (one that is not yet complete or canceled and should be displayed in the default list)', verbose_name='is active')),
                ('is_default', models.BooleanField(default=False, help_text='If this is the default status for new loads (Only one will used even if more than one is selected)', verbose_name='is default')),
            ],
            options={
                'ordering': ('list_order', 'name'),
            },
        ),
        migrations.AddField(
            model_name='item',
            name='status_new',
            field=models.ForeignKey(help_text='The status of this project', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.status'),
        ),
    ]