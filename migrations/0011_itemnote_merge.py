from django.db import migrations, models
import django.db.models.deletion

def forwards(apps, schema_editor):
    try:
        TimelyNote = apps.get_model('libtekin', 'TimelyNote')

        for timelynote in TimelyNote.objects.all():
            itemnote=ItemNote(
                when=timelynote.when,
                text=timelynote.text,
                is_major=timelynote.is_current_status,
                item=timelynote.item
            )
            itemnote.save()

    except LookupError:
        pass

    try:
        UntimedNote = apps.get_model('libtekin', 'UntimedNote')

        for untimednote in UntimedNote.objects.all():
            itemnote=ItemNote(
                text=untimednote.subject + ":" + untimednote.text,
                is_major=untimednote.is_major,
                item=untimednote.item
            )
            itemnote.save()

    except LookupError:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('libtekin', '0010_itemnote'),
    ]
    operations = [
        migrations.RunPython(forwards)
    ]
