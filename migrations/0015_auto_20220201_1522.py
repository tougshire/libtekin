# Generated by Django 3.2.9 on 2022-02-01 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0014_alter_item_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='essid',
            field=models.CharField(blank=True, help_text="The device's ESSID", max_length=100, verbose_name='ESSID'),
        ),
        migrations.AddField(
            model_name='item',
            name='phone_number',
            field=models.CharField(blank=True, help_text='The phone number of the device', max_length=100, verbose_name='phone_number'),
        ),
        migrations.AlterField(
            model_name='item',
            name='primary_id_field',
            field=models.CharField(blank=True, choices=[('serial_number', 'Serial Number'), ('service_number', 'Service Number'), ('asset_number', 'Asset Number'), ('barcode', 'Barcode'), ('phone_number', 'Phone Number'), ('essid', 'ESSID')], help_text='The identifier which is the primary id', max_length=50, verbose_name='primary id is'),
        ),
        migrations.AlterField(
            model_name='mmodel',
            name='primary_id_field',
            field=models.CharField(blank=True, choices=[('serial_number', 'Serial Number'), ('service_number', 'Service Number'), ('asset_number', 'Asset Number'), ('barcode', 'Barcode'), ('phone_number', 'Phone Number'), ('essid', 'ESSID')], help_text='By default, the field which should be used as the primary ID field (ex: "SN", "Tag Number", etc)', max_length=50, verbose_name='Primary ID Field'),
        ),
    ]
