from django.conf import settings
from django.forms import ModelForm, inlineformset_factory, Select
from django.urls import reverse_lazy
from .models import (
    Entity,
    Item,
    ItemAssignee,
    ItemBorrower,
    ItemNote,
    ItemNoteCategory,
    Location,
    Mmodel,
    MmodelCategory,
)
from django import forms
from touglates.widgets import TouglateDateInput, TouglateRelatedSelect


class MmodelSelect(Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value:
            option["attrs"]["data-primary_id_field"] = value.instance.primary_id_field
        return option


class ItemSelect(Select):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value:
            # data-textforfilter provides additional fields that can be used for filtering
            option["attrs"]["data-textforfilter"] = "{} {}".format(
                value.instance.mmodel, value.instance.primary_id
            )
        return option


class EntityForm(ModelForm):
    class Meta:
        model = Entity
        fields = [
            "friendly_name",
            "full_name",
            "category",
        ]


class ItemForm(ModelForm):
    def __init__(self, *args, **kwargs):
        init = super().__init__(*args, **kwargs)

        if hasattr(settings, "LIBTEKIN_ID_CHOICES"):
            primary_id_choices = settings.LIBTEKIN_ID_CHOICES
        else:
            primary_id_choices = Mmodel.ID_CHOICES
        self.fields["primary_id_field"].widget = forms.Select(
            choices=primary_id_choices
        )

        return init

    class Meta:
        model = Item
        fields = [
            "common_name",
            "mmodel",
            "primary_id_field",
            "serial_number",
            "service_number",
            "asset_number",
            "barcode",
            "phone_number",
            "essid",
            "connected_to",
            "status",
            "network_name",
            "owner",
            "home",
            "latest_inventory",
            "installation_date",
            "location",
            "role",
        ]
        widgets = {
            "mmodel": MmodelSelect,
            "connected_to": MmodelSelect,
            "latest_inventory": TouglateDateInput(),
            "installation_date": forms.DateInput(attrs={"type": "date"}),
        }


class ItemBorrowerForm(ModelForm):
    class Meta:
        model = ItemBorrower
        fields = [
            "item",
            "entity",
            "when",
        ]
        widgets = {
            "entity": TouglateRelatedSelect(
                related_data={
                    "model": "Entity",
                    "add_url": reverse_lazy("libtekin:item-entity-create"),
                }
            ),
        }


class ItemAssigneeForm(ModelForm):
    class Meta:
        model = ItemAssignee
        fields = [
            "item",
            "entity",
            "when",
        ]
        widgets = {
            "entity": TouglateRelatedSelect(
                related_data={
                    "model": "Entity",
                    "add_url": reverse_lazy("libtekin:item-entity-create"),
                }
            ),
        }


class ItemNoteForm(ModelForm):
    class Meta:
        model = ItemNote
        fields = [
            "item",
            "when",
            "level",
            "flagged",
            "itemnotecategory",
            "maintext",
            "details",
        ]
        widgets = {
            "item": ItemSelect(),
            "when": forms.DateInput(attrs={"type": "date"}),
            "maintext": forms.TextInput(attrs={"class": "widthlong"}),
            "details": forms.Textarea(attrs={"class": "widthlong"}),
        }


class ItemNoteCategoryForm(ModelForm):
    class Meta:
        model = ItemNoteCategory
        fields = [
            "name",
        ]


class MmodelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        init = super().__init__(*args, **kwargs)

        if hasattr(settings, "LIBTEKIN_ID_CHOICES"):
            primary_id_choices = settings.LIBTEKIN_ID_CHOICES
        else:
            primary_id_choices = Mmodel.ID_CHOICES
        self.fields["primary_id_field"].widget = forms.Select(
            choices=primary_id_choices
        )

        return init

    class Meta:
        model = Mmodel
        fields = ["brand", "model_name", "model_number", "category", "primary_id_field"]


class MmodelCategoryForm(ModelForm):
    class Meta:
        model = MmodelCategory
        fields = [
            "name",
        ]


class LocationForm(ModelForm):
    class Meta:
        model = Location
        fields = ["full_name", "short_name", "category"]


class ItemCopyForm(forms.Form):
    qty = forms.IntegerField()


ItemItemNoteFormset = inlineformset_factory(Item, ItemNote, form=ItemNoteForm, extra=10)
ItemBorrowerFormset = inlineformset_factory(
    Item, ItemBorrower, form=ItemBorrowerForm, extra=10
)
ItemAssigneeFormset = inlineformset_factory(
    Item, ItemAssignee, form=ItemAssigneeForm, extra=10
)
