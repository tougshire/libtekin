from datetime import date, datetime, timedelta
from django.utils import timezone

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db import models
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Concat
from django.urls import reverse
from spl_members.models import Member


def get_default_status():
    try:
        return Status.objects.filter(is_default=True).first().pk
    except AttributeError:
        return None


def get_default_level():
    try:
        return ItemNoteLevel.objects.filter(number=0).first().pk
    except AttributeError:
        return None


class EntityCategory(models.Model):
    name = models.CharField(
        "name",
        max_length=75,
        help_text='The name of the entity category, like "Person" or "Organization"',
    )
    sort_name = models.CharField(
        "sort name",
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "C Organization"',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["sort_name", "name"]


class Entity(models.Model):
    friendly_name = models.CharField(
        "friendly name",
        max_length=25,
        blank=True,
        help_text='The friendly name for this person or organization, like "Ben" or "IT"',
    )
    full_name = models.CharField(
        "full name",
        max_length=75,
        help_text='The full name for this person or organization, like "Benjamin Goldberg" or "Suffolk Information Technology Division"',
    )
    category = models.ForeignKey(
        EntityCategory,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The type of entity",
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ["full_name"]


class LocationCategory(models.Model):
    name = models.CharField(
        "name",
        max_length=75,
        help_text='The name of the location category, like "Library Location"',
    )
    sort_name = models.CharField(
        "sort name",
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Library Location"',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["sort_name", "name"]


class Location(models.Model):
    short_name = models.CharField(
        "short name",
        max_length=25,
        blank=True,
        help_text='The short name for this location, like "MML"',
    )
    full_name = models.CharField(
        "full name",
        max_length=75,
        help_text='The full name for this location, like "Morgan Memorial Library',
    )
    category = models.ForeignKey(
        LocationCategory,
        verbose_name="category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The category of this location",
    )

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ["full_name"]


class MmodelCategory(models.Model):
    name = models.CharField(
        "name",
        max_length=75,
        help_text='The name of the category, like "Laptop Computer"',
    )
    sort_name = models.CharField(
        "sort name",
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Laptops"',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["sort_name"]


class Mmodel(models.Model):
    ID_CHOICES = [
        ("serial_number", "Serial Number"),
        ("bios_serial_number", "Bios Serial Number"),
        ("asset_number", "Asset Number"),
        ("barcode", "Barcode"),
    ]

    brand = models.CharField(
        "brand",
        max_length=75,
        help_text="The brand name of the item or the manufacturer, or supplier, etc..",
    )
    model_name = models.CharField(
        "model_name", max_length=75, help_text='The model name, like "Latitude 3390"'
    )
    model_number = models.CharField(
        "model_number",
        max_length=75,
        blank=True,
        help_text="The model number if different than model name",
    )
    category = models.ForeignKey(
        MmodelCategory,
        verbose_name="category",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The category, such as Laptop or Phone, to which this item belongs",
    )
    primary_id_field = models.CharField(
        "Primary ID Field",
        max_length=50,
        blank=True,
        help_text='By default, the field which should be used as the primary ID field (ex: "SN", "Tag Number", etc)',
    )

    def __str__(self):
        return f"{self.brand} {self.model_name}"

    class Meta:
        ordering = ["brand", "model_name"]
        verbose_name = "model"


class Role(models.Model):
    name = models.CharField(
        "name", max_length=75, help_text='The name of the role ("Public", "Staff", etc)'
    )
    sort_name = models.CharField(
        "sort name",
        max_length=25,
        blank=True,
        help_text='A name for sorting, not normally displayed.  This can be as simple as "A","B", or "C", or something like "B Public"',
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["sort_name", "name"]


class Status(models.Model):
    name = models.CharField(max_length=50, help_text="The status of the item")
    list_position = models.IntegerField(
        "rank",
        default=1000,
        help_text="The order that this status should display in a list of statuses",
    )
    is_active = models.BooleanField(
        "is active", default=False, help_text="If this status is for an active item)"
    )
    is_default = models.BooleanField(
        "is default",
        default=False,
        help_text="If this is the default status for new items (Only one will used even if more than one is selected)",
    )

    class Meta:
        ordering = (
            "list_position",
            "name",
        )

    def __str__(self):
        return self.name


class ItemNotDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ItemAllManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class Item(models.Model):
    common_name = models.CharField(
        "common name",
        max_length=75,
        blank=True,
        help_text='The common name for this piece of equipment, like "Ben\'s Laptop"',
    )
    mmodel = models.ForeignKey(
        Mmodel,
        verbose_name="model",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The items model",
    )
    primary_id = models.CharField(
        "primary ID",
        max_length=100,
        blank=True,
        help_text="The primary ID used for this item",
    )
    primary_id_field = models.CharField(
        "primary id field",
        max_length=50,
        blank=True,
        help_text="The identifier which is the primary id",
    )
    network_name = models.CharField(
        "network name", max_length=100, blank=True, help_text="The item's network name"
    )
    serial_number = models.CharField(
        "serial number",
        max_length=100,
        blank=True,
        help_text="The serial number or alternate ID which is used as the serial number",
    )
    bios_serial_number = models.CharField(
        "bios serial number",
        max_length=100,
        blank=True,
        help_text="The serial number stored in bios used by several computer manufacturers",
    )
    asset_number = models.CharField(
        "asset number",
        max_length=100,
        blank=True,
        help_text="The local inventory number for this item",
    )
    barcode = models.CharField(
        "barcode",
        max_length=100,
        blank=True,
        help_text="The barcode attached to this item",
    )
    phone_number = models.CharField(
        "phone_number",
        max_length=100,
        blank=True,
        help_text="The phone number of the device",
    )
    mobile_id = models.CharField(
        "Mobile ID",
        max_length=100,
        blank=True,
        help_text="The device's IMEI, MEID, SSID, etc..",
    )
    sim_iccid = models.CharField(
        "SIM iccid", max_length=100, blank=True, help_text="The id of the SIM card"
    )
    owner = models.ForeignKey(
        Entity,
        verbose_name="owner",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_owned",
        help_text="The owner of the item",
    )
    assignee = models.ForeignKey(
        Member,
        verbose_name="member assignee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_assigned_to_member",
        help_text="The responsible party for the item",
    )
    borrower = models.ForeignKey(
        Member,
        verbose_name="member borrower",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_borrowed_to_member",
        help_text="The temporary user of the item",
    )

    home = models.ForeignKey(
        Location,
        verbose_name="home",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_homed",
        help_text="The home location of this item",
    )
    location = models.ForeignKey(
        Location,
        verbose_name="location",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="item_located",
        help_text="The current location of this item",
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.SET_NULL,
        null=True,
        default=get_default_status,
        help_text="The status of this item",
    )
    role = models.ForeignKey(
        Role,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The roles to which this item belongs",
    )
    connected_to = models.ForeignKey(
        "Item",
        verbose_name="connected to",
        related_name="connection",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="For peripherals and components, the device to which this item is connected. For example, if this item is a monitor, choose its computer.  If this is the computer, do not enter the monitor here",
    )
    installation_date = models.DateField(
        "Installation Date",
        null=True,
        blank=True,
        default=date.today,
        help_text="The date that this item was installed",
    )
    latest_inventory = models.DateField(
        "Latest Inventory Date",
        null=True,
        blank=True,
        default=date.today,
        help_text="The date that this item was last confirmed in inventory",
    )
    is_deleted = models.BooleanField(
        "is deleted", default=False, help_text="If this item is deleted"
    )

    def get_absolute_url(self):
        return reverse("libtekin:item-detail", kwargs={"pk": self.pk})

    def get_current__status_notes(self):
        current_notes = []
        for note in self.itemnote_set.filter(flagged_gt=0):
            current_notes.append(
                "{}: {}".format(note.when.strftime("%Y-%m-%d"), note.text)
            )

        return current_notes
        # return separator.join(current_notes)

    def save(self, *args, **kwargs):
        if self.primary_id_field:
            setattr(self, "primary_id", getattr(self, self.primary_id_field))

        saved = super().save(*args, **kwargs)

        item_assignee_recents = ItemAssignee.objects.filter(
            item=self,
            assignee=self.assignee,
            when__gte=datetime.now() + timedelta(hours=-1),
        )
        if item_assignee_recents.exists():
            if item_assignee_recents.last() != self.assignee:
                ItemAssignee.objects.create(item=self, assignee=self.assignee)
        else:
            ItemAssignee.objects.create(item=self, assignee=self.assignee)


        item_borrower_recents = ItemBorrower.objects.filter(
            item=self,
            borrower=self.borrower,
            when__gte=datetime.now() + timedelta(hours=-1),
        )
        if not item_borrower_recents.exists():
            ItemBorrower.objects.create(item=self, borrower=self.borrower)

        return saved

    def __str__(self):
        if self.common_name:
            return f"{self.common_name}"
        elif self.primary_id:
            return f"{self.primary_id}"
        else:
            return self.pk

    class Meta:
        ordering = ["primary_id"]

    objects = ItemNotDeletedManager()
    all_objects = ItemAllManager()


class ItemAssignee(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The item to which assignment applies",
        related_name="historical_assignements",
    )

    assignee = models.ForeignKey(
        Member,
        verbose_name="member assignee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historical_assignements",
        help_text="The current responsible party for the item",
    )

    when = models.DateTimeField(
        "when",
        blank=True,
        null=True,
        default=timezone.now,
        help_text="The effective date of the assignment",
    )

    class Meta:
        ordering = ["-when", "-pk"]

    def __str__(self):
        return f"{self.assignee} -> {self.item}"


class ItemBorrower(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The item to which this loan applies",
        related_name="historical_borrow",
    )
    borrower = models.ForeignKey(
        Member,
        verbose_name="member borrower",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historical_borrow",
        help_text="The user of the item",
    )
    when = models.DateField(
        "when",
        blank=True,
        null=True,
        default=date.today,
        help_text="The effective date of the loan",
    )

    class Meta:
        ordering = ["-when", "-pk"]

    def __str__(self):
        return f"{self.assignee} -> {self.item} "


class ItemNoteLevel(models.Model):
    name = models.CharField(max_length=50, help_text="The name of the level")
    number = models.IntegerField(
        "numeric value",
        default=0,
        help_text="The value of the level, with 0 being info only and a higher number, such as 5 being critical",
    )

    class Meta:
        ordering = (
            "number",
            "name",
        )

    def __str__(self):
        return "{}: {}".format(self.number, self.name)


class ItemNoteCategory(models.Model):
    name = models.CharField("Name", max_length=50, help_text="The category name")

    def __str__(self):
        return self.name


class ItemNote(models.Model):
    item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The item to which this note applies",
    )
    when = models.DateField(
        "when",
        blank=True,
        null=True,
        default=date.today,
        help_text="The effective date of the information in the note ( rather than the date the note was made )",
    )
    itemnotecategory = models.ForeignKey(
        ItemNoteCategory,
        verbose_name="Category",
        on_delete=models.SET_NULL,
        null=True,
        help_text="The category for this note",
    )
    maintext = models.CharField(
        "description",
        max_length=125,
        blank=True,
        help_text="The text of the note.  Optional if a category is chosen and no other details are necessary.",
    )
    details = models.TextField(
        "details",
        blank=True,
        help_text="The details of the note if the description text is not sufficient",
    )
    endtext = models.CharField(
        "end comment",
        max_length=125,
        blank=True,
        help_text='For temporary situations, comments regarding the end of the situation (ex: "memory card replaced")',
    )
    level = models.ForeignKey(
        ItemNoteLevel,
        default=get_default_level,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The level of this note",
    )
    flagged = models.IntegerField(
        "flagged",
        default=0,
        choices=((1, "Yes"), (0, "No")),
        help_text="If this note is flagged for viewing by default in an item detail view",
    )

    def __str__(self):
        str = ""
        if self.when:
            str = str + self.when.isoformat() + ": "
        if self.level:
            str = str + self.level.name + ": "
        if self.itemnotecategory:
            str = str + self.itemnotecategory.name + ": "
        if self.maintext:
            str = str + self.maintext + ": "
        if len(str) > 2:
            str = str[0:-2]
        if len(str) > 50:
            str = str[0:45] + " ..."

        return str

    class Meta:
        ordering = [
            "-when",
        ]


class History(models.Model):
    when = models.DateTimeField(
        "when", auto_now_add=True, help_text="The date this change was made"
    )
    modelname = models.CharField(
        "model", max_length=50, help_text="The model to which this change applies"
    )
    objectid = models.BigIntegerField(
        "object id",
        null=True,
        blank=True,
        help_text="The id of the record that was changed",
    )
    fieldname = models.CharField(
        "field",
        max_length=50,
        help_text="The that was changed",
    )
    old_value = models.TextField(
        "old value",
        blank=True,
        null=True,
        help_text="The value of the field before the change",
    )
    new_value = models.TextField(
        "new value", blank=True, help_text="The value of the field after the change"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The user who made this change",
    )

    class Meta:
        ordering = ("-when", "modelname", "objectid")

    def __str__(self):
        new_value_trunc = (
            self.new_value[:17:] + "..." if len(self.new_value) > 20 else self.new_value
        )

        try:
            model = apps.get_model("libtekin", self.modelname)
            object = model.objects.get(pk=self.objectid)
            return f'{self.when.strftime("%Y-%m-%d")}: {self.modelname}: [{object}] [{self.fieldname}] changed to "{new_value_trunc}"'

        except Exception as e:
            print(e)

        return f'{"mdy".format(self.when.strftime("%Y-%m-%d"))}: {self.modelname}: {self.objectid} [{self.fieldname}] changed to "{new_value_trunc}"'
