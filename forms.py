from django.forms import ModelForm, inlineformset_factory, Select
from .models import Entity, Item, TimelyNote, UntimedNote, Location, Mmodel, MmodelCategory
from django import forms

class EntityForm(ModelForm):
    class Meta:
        model = Entity
        fields = [
            'friendly_name',
            'full_name',
            'category',
        ]

class MmodelSelect(Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option['attrs']['data-primary_id_field'] = value.instance.primary_id_field
        return option

class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = [
            'common_name',
            'mmodel',
            'primary_id_field',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'condition',
            'network_name',
            'assignee',
            'owner',
            'borrower',
            'home',
            'latest_inventory',
            'location',
            'role',
        ]
        widgets = {
            'mmodel': MmodelSelect,
            'latest_inventory':forms.DateInput( attrs={ "type":"date" } ),
        }

class TimelyNoteForm(ModelForm):
    class Meta:
        model = TimelyNote
        fields = [
            'item',
            'when',
            'text',
            'is_current_status',
        ]

class MmodelForm(ModelForm):
    class Meta:
        model = Mmodel
        fields = [
            'brand',
            'model_name',
            'model_number',
            'category',
            'primary_id_field'
        ]

class MmodelCategoryForm(ModelForm):
    class Meta:
        model = MmodelCategory
        fields = [
            'name',
        ]


class LocationForm(ModelForm):
    class Meta:
        model = Location
        fields = [
            'full_name',
            'short_name',
            'category'
        ]

class UntimedNoteForm(ModelForm):
    class Meta:
        model = UntimedNote
        fields = [
            'item',
            'subject',
            'text',
            'is_major',
        ]


ItemTimelyNoteFormSet = inlineformset_factory(Item, TimelyNote, TimelyNoteForm, extra=0)
ItemUntimedNoteFormSet = inlineformset_factory(Item, UntimedNote, UntimedNoteForm, extra=0)
