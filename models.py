from django.core import exceptions
from django.db import models
from django.urls import reverse
from datetime import date
from django.conf import settings
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

class Condition(models.Model):
    name = models.CharField(
        'name',
        max_length=75,
        help_text='The name of the condition ("Good", "Usable with Issues", "Inoperative", etc)'
    )
    sort_name = models.CharField(
        'sort name',
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "D Inoperative"'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_name', 'name']

class EntityCategory(models.Model):
    name = models.CharField(
        'name',
        max_length=75,
        help_text='The name of the entity category, like "Person" or "Organization"'
    )
    sort_name = models.CharField(
        'sort name',
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "C Organization"'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_name', 'name']

class Entity(models.Model):

    friendly_name = models.CharField(
        'friendly name',
        max_length=25,
        blank=True,
        help_text='The friendly name for this person or organization, like "Ben" or "IT"'
    )
    full_name = models.CharField(
        'full name',
        max_length=75,
        help_text='The full name for this person or organization, like "Benjamin Goldberg" or "Suffolk Information Technology Division"',
    )
    category = models.ForeignKey(
        EntityCategory,
        on_delete = models.SET_NULL,
        null=True,
        help_text = 'The type of entity'
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']

class LocationCategory(models.Model):

    name = models.CharField(
        'name',
        max_length=75,
        help_text='The name of the location category, like "Library Location"'
    )
    sort_name = models.CharField(
        'sort name',
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Library Location"'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_name', 'name']

class Location(models.Model):

    short_name = models.CharField(
        'short name',
        max_length=25,
        blank=True,
        help_text='The short name for this location, like "MML"'
    )
    full_name = models.CharField(
        'full name',
        max_length=75,
        help_text='The full name for this location, like "Morgan Memorial Library'
    )
    category = models.ForeignKey(
        LocationCategory,
        verbose_name='category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='The category of this location'
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']


class MmodelCategory(models.Model):

    name = models.CharField(
        'name',
        max_length=75,
        help_text='The name of the category, like "Laptop Computer"'
    )
    sort_name = models.CharField(
        'sort name',
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Laptops"'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_name']

class Mmodel(models.Model):

    if hasattr(settings,'LIBTEKIN_ID_CHOICES'):
        ID_CHOICES=settings.LIBTEKIN_ID_CHOICES
    else:
        ID_CHOICES=[
            ('serial_number', 'Serial Number'),
            ('service_number', 'Service Number'),
            ('asset_number', 'Asset Number'),
        ]

    brand = models.CharField(
        'brand',
        max_length=75,
        help_text='The brand name of the item or the manufacturer, or supplier, etc..'
    )
    model_name = models.CharField(
        'model_name',
        max_length=75,
        help_text='The model name, like "Latitude 3390"'
    )
    model_number = models.CharField(
        'model_number',
        max_length=75,
        blank=True,
        help_text='The model number if different than model name'
    )
    category = models.ForeignKey(
        MmodelCategory,
        verbose_name='category',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='The category, such as Laptop or Phone, to which this item belongs'
    )
    primary_id_field = models.CharField(
        'Primary ID Field',
        max_length=50,
        choices=ID_CHOICES,
        blank=True,
        help_text='By default, the field which should be used as the primary ID field (ex: "SN", "Tag Number", etc)'
    )

    def __str__(self):
        return f'{self.brand} {self.model_name}'

    class Meta:
        ordering = [ 'brand', 'model_name' ]
        verbose_name = 'model'

class Role(models.Model):
    name = models.CharField(
        'name',
        max_length=75,
        help_text='The name of the role ("Public", "Staff", etc)'
    )
    sort_name = models.CharField(
        'sort name',
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Public"'
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['sort_name', 'name']

class ItemNotDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class Item(models.Model):

    common_name = models.CharField(
        'common name',
        max_length=75,
        blank=True,
        help_text='The common name for this piece of equipment, like "Ben\'s Laptop"'
    )
    mmodel = models.ForeignKey(
        Mmodel,
        verbose_name='model',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='The items model'
    )
    primary_id = models.CharField(
        'primary ID',
        max_length=100,
        blank=True,
        help_text='The primary ID used for this item'
    )
    primary_id_field = models.CharField(
        'primary id is',
        max_length=50,
        choices=Mmodel.ID_CHOICES,
        blank=True,
        help_text='The identifier which is the primary id'
    )
    network_name = models.CharField(
        'network name',
        max_length=100,
        blank=True,
        help_text='The item\'s network name'
    )
    serial_number = models.CharField(
        'serial number',
        max_length=100,
        blank=True,
        help_text='The serial number or alternate ID (service tag or asset number) which is used as the serial number'
    )
    service_number = models.CharField(
        'service number',
        max_length=100,
        blank=True,
        help_text='The serial number or alternate ID (service tag or asset number) which is considered second to the primary ID'
    )
    asset_number = models.CharField(
        'asset number',
        max_length=100,
        blank=True,
        help_text='The local inventory number for this item'
    )
    barcode = models.CharField(
        'barcode',
        max_length=100,
        blank=True,
        help_text='The barcode attached to this item'
    )
    phone_number = models.CharField(
        'phone_number',
        max_length=100,
        blank=True,
        help_text='The phone number of the device'
    )
    essid = models.CharField(
        'ESSID',
        max_length=100,
        blank=True,
        help_text='The device\'s ESSID'
    )
    owner = models.ForeignKey(
        Entity,
        verbose_name='owner',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_owned',
        help_text='The owner of the item'
    )
    assignee = models.ForeignKey(
        Entity,
        verbose_name='assignee',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_assigned',
        help_text='The current responsible party for the item'
    )
    borrower = models.ForeignKey(
        Entity,
        verbose_name='borrower',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_borrowed',
        help_text='The current holder the item'
    )
    home = models.ForeignKey(
        Location,
        verbose_name='home',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_homed',
        help_text='The home location of this item',
    )
    location = models.ForeignKey(
        Location,
        verbose_name='location',
        on_delete = models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_located',
        help_text='The current location of this item',
    )
    condition = models.ForeignKey(
        Condition,
        on_delete=models.SET_NULL,
        null=True,
        help_text='The condition of this item'
    )
    role = models.ForeignKey(
        Role,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text='The roles to which this item belongs'
    )
    latest_inventory = models.DateField(
        'Latest Inventory Date',
        null=True,
        blank=True,
        default=date.today,
        help_text='The date that this item was last confirmed in inventory'
    )
    is_deleted = models.BooleanField(
        'is deleted',
        default=False,
        help_text = 'If this item is deleted'
    )

    def save(self, *args, **kwargs):
        if(self.primary_id_field):
            setattr(self, 'primary_id', getattr(self, self.primary_id_field))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('libtekin:item-detail', kwargs={'pk':self.pk})

    def __str__(self):
        return f'{self.common_name}'

    class Meta:
        ordering = ['primary_id']

    objects = ItemNotDeletedManager()
    all_objects = models.Manager()

class ItemNote(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        help_text='The item to which this note applies'
    )
    when = models.DateField(
        'when',
        blank=True,
        null=True,
        help_text="Can be blank for notes that don't represent events.  If filled, consider the effective date of the information rather than the date the note was made"
    )
    text = models.CharField(
        max_length=125,
        blank=True,
        help_text='The text of the note.  Can be a subject line or introduction if more is included in details'
    )
    details = models.TextField(
        'details',
        blank=True,
        help_text='The details of the note if the summary is not sufficient'
    )
    is_major = models.BooleanField(
        'is major or current status',
        default=False,
        help_text='If this note is diplayed by default in the item detail view.  If not, it will be displayed when "Show All" is selected'
    )

    def __str__(self):
        return f'{self.when.isoformat()}: {self.text}' if self.when else self.text

    class Meta:
        ordering = ['-when', 'text']

class History(models.Model):

    when = models.DateTimeField(
        'when',
        auto_now_add=True,
        help_text='The date this change was made'
    )
    modelname = models.CharField(
        'model',
        max_length=50,
        help_text='The model to which this change applies'
    )
    objectid = models.BigIntegerField(
        'object id',
        null=True,
        blank=True,
        help_text='The id of the record that was changed'
    )
    fieldname = models.CharField(
        'field',
        max_length=50,
        help_text='The that was changed',
    )
    old_value = models.TextField(
        'old value',
        blank=True,
        null=True,
        help_text='The value of the field before the change'
    )
    new_value = models.TextField(
        'new value',
        blank=True,
        help_text='The value of the field after the change'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text='The user who made this change'
    )

    class Meta:
        ordering = ('-when', 'modelname', 'objectid')

    def __str__(self):

        new_value_trunc = self.new_value[:17:]+'...' if len(self.new_value) > 20 else self.new_value

        try:
            model = apps.get_model('libtekin', self.modelname)
            object = model.objects.get(pk=self.objectid)
            return f'{self.when.strftime("%Y-%m-%d")}: {self.modelname}: [{object}] [{self.fieldname}] changed to "{new_value_trunc}"'

        except Exception as e:
            print (e)

        return f'{"mdy".format(self.when.strftime("%Y-%m-%d"))}: {self.modelname}: {self.objectid} [{self.fieldname}] changed to "{new_value_trunc}"'
