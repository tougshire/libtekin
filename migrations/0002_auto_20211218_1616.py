# Generated by Django 3.2.9 on 2021-12-18 21:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The name of the role ("Public", "Staff", etc)', max_length=75, verbose_name='name')),
                ('sort_name', models.CharField(blank=True, help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Public"', max_length=25, verbose_name='sort name')),
            ],
            options={
                'ordering': ['sort_name', 'name'],
            },
        ),
        migrations.AddField(
            model_name='item',
            name='role',
            field=models.ForeignKey(blank=True, help_text='The roles to which this item belongs', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.role'),
        ),
    ]
