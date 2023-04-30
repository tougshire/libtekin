# Generated by Django 4.1.7 on 2023-04-28 18:23

from django.db import migrations, models
import django.db.models.deletion
import libtekin.models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0032_alter_itemnote_options_remove_itemnote_text_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ItemNoteCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The category name', max_length=50, verbose_name='Name')),
            ],
        ),
        migrations.AlterField(
            model_name='item',
            name='status',
            field=models.ForeignKey(default=libtekin.models.get_default_status, help_text='The status of this item', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.status'),
        ),
        migrations.AddField(
            model_name='itemnote',
            name='itemnotecategory',
            field=models.ForeignKey(blank=True, help_text='The optional category for this note', null=True, on_delete=django.db.models.deletion.SET_NULL, to='libtekin.itemnotecategory', verbose_name='Category'),
        ),
    ]
