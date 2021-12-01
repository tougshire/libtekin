from django.forms import ModelForm, inlineformset_factory
from .models import Entity, Item, ItemNote, Location, Mmodel, MmodelCategory

class EntityForm(ModelForm):
    class Meta:
        model = Entity
        fields = [
            'friendly_name',
            'full_name',
        ]

class ItemForm(ModelForm):
    class Meta:
        model = Item
        fields = [
            'common_name',
            'mmodel',
            'primary_id_is',
            'serial_number',
            'service_number',
            'asset_number',
            'condition',
            'network_name',
            'assignee',
            'owner',
            'borrower',
            'home',
            'location',
            'barcode'
        ]

class ItemNoteForm(ModelForm):
    class Meta:
        model = ItemNote
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
            'categories',
            'primary_id_is'
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

ItemItemNoteFormSet = inlineformset_factory(Item, ItemNote, ItemNoteForm, extra=0)
