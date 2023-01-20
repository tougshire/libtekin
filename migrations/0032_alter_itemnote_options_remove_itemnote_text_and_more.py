# Generated by Django 4.1.2 on 2023-01-15 13:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0031_alter_itemnote_details'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='itemnote',
            options={'ordering': ['-when']},
        ),
        migrations.RenameField(
            model_name='itemnote',
            old_name='text',
            new_name='maintext',
        ),
        migrations.AlterField(
            model_name='itemnote',
            name='maintext',
            field=models.CharField(blank=True, help_text='The text of the note.  Can be a subject line or introduction if more is included in details', max_length=125, verbose_name='description'),
        ),

    ]