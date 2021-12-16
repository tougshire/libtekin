# Generated by Django 3.2.9 on 2021-12-16 00:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mmodel',
            name='categories',
            field=models.ManyToManyField(blank=True, help_text='The categories , such as Laptop or Phone, to which this item belongs', to='libtekin.MmodelCategory', verbose_name='categories'),
        ),
    ]
