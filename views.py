import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.core.exceptions import FieldError, ObjectDoesNotExist
from .forms import EntityForm, ItemForm, TimelyNoteForm, ItemTimelyNoteFormSet, ItemUntimedNoteFormSet, LocationForm, MmodelForm, MmodelCategoryForm
from .models import Condition, Entity, Item, TimelyNote, UntimedNote, Location, Mmodel, MmodelCategory, Role, History
from tougshire_vistas.models import Vista
from tougshire_vistas.views import get_vista_object

def update_history(form, modelname, object, user):
    for fieldname in form.changed_data:
        try:
            old_value=str(form.initial[fieldname]),
        except KeyError:
            old_value=None

        history = History.objects.create(
            user=user,
            modelname=modelname,
            objectid=object.pk,
            fieldname=fieldname,
            old_value=old_value,
            new_value=str(form.cleaned_data[fieldname])
        )

        history.save()

class ItemCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_item'
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        if self.request.POST:
            context_data['timelynotes'] = ItemTimelyNoteFormSet(self.request.POST)
            context_data['untimednotes'] = ItemUntimedNoteFormSet(self.request.POST)

        else:
            context_data['timelynotes'] = ItemTimelyNoteFormSet()
            context_data['untimednotes'] = ItemUntimedNoteFormSet()

        return context_data

    def form_valid(self, form):

        response = super().form_valid(form)

        update_history(form, 'Item', form.instance, self.request.user)

        self.object = form.save()

        timelynotes = ItemTimelyNoteFormSet(self.request.POST, instance=self.object)

        if timelynotes.is_valid():
            for form in timelynotes.forms:
                update_history(form, 'TimelyNote', form.instance, self.request.user)

            timelynotes.save()
        else:
            print("formset is not not valid")
            print(timelynotes.errors)
            for form in timelynotes.forms:
                print( form.errors )

        untimednotes = ItemUntimedNoteFormSet(self.request.POST, instance=self.object)

        if untimednotes.is_valid():
            for form in untimednotes.forms:
                update_history(form, 'UntimedNote', form.instance, self.request.user)

            untimednotes.save()
        else:
            print("formset is not not valid")
            print(untimednotes.errors)
            for form in untimednotes.forms:
                print( form.errors )

        return response

    def get_success_url(self):
        if 'opener' in self.request.POST and self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:item-close', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('libtekin:item-detail', kwargs={'pk': self.object.pk})



class ItemUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_item'
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.request.POST:
            context_data['timelynotes'] = ItemTimelyNoteFormSet(self.request.POST, instance=self.object)
            context_data['untimednotes'] = ItemUntimedNoteFormSet(self.request.POST, instance=self.object)
        else:
            context_data['timelynotes'] = ItemTimelyNoteFormSet(instance=self.object)
            context_data['untimednotes'] = ItemUntimedNoteFormSet(instance=self.object)

        return context_data

    def form_valid(self, form):

        if 'copy' in self.request.POST:
            form.instance.pk=None

        update_history(form, 'Item', form.instance, self.request.user)

        response = super().form_valid(form)

        timelynotes = ItemTimelyNoteFormSet(self.request.POST, instance=self.object)

        if timelynotes.is_valid():

            for form in timelynotes.forms:
                update_history(form, 'Item', form.instance, self.request.user)

            timelynotes.save()
        else:
            print("formset is not not valid")
            print(timelynotes.errors)
            for form in timelynotes.forms:
                print( form.errors )

        untimednotes = ItemUntimedNoteFormSet(self.request.POST, instance=self.object)

        if untimednotes.is_valid():

            for form in untimednotes.forms:
                update_history(form, 'Item', form.instance, self.request.user)

            untimednotes.save()
        else:
            print("formset is not not valid")
            print(untimednotes.errors)
            for form in untimednotes.forms:
                print( form.errors )



        return response

    def get_success_url(self):
        return reverse_lazy('libtekin:item-detail', kwargs={ 'pk':self.object.pk })


class ItemDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_item'
    model = Item

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['timelynote_labels'] = { field.name: field.verbose_name.title() for field in TimelyNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemDelete(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.delete_item'
    model = Item
    success_url = reverse_lazy('libtekin:item-list')

class ItemSoftDelete(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.delete_item'
    model = Item
    template_name = 'libtekin/item_confirm_delete.html'
    success_url = reverse_lazy('libtekin:item-list')
    fields = ['is_deleted']

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['current_notes'] = self.object.timelynote_set.all().filter(is_current_status=True)
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['timelynote_labels'] = { field.name: field.verbose_name.title() for field in TimelyNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_item'
    model = Item
    filter_object = {}
    exclude_object = {}
    order_by = []
    order_by_fields=[]
    common_text_search=""
    common_text_fields=[
            'common_name',
            'mmodel__model_name',
            'mmodel__category__name',
            'mmodel__brand',
            'primary_id',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'network_name',
    ]

    for fieldname in ['common_name', 'mmodel', 'primary_id', 'serial_number','service_number']:
        order_by_fields.append(
            { 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title() }
        )
        order_by_fields.append(
            { 'name':'-' + fieldname, 'label':'{} reverse'.format(Item._meta.get_field(fieldname).verbose_name.title()) }
        )
    filter_fields = {
        'in':['mmodel', 'mmodel__category', 'condition', 'role']
    }
    showable_fields = []
    shown_fields = []
    for fieldname in [
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
            'location',
            'role',
        ]:
        showable_fields.append(
            {
                'name':fieldname,
                'label':Item._meta.get_field(fieldname).verbose_name.title()
            }
        )
        shown_fields.append(fieldname)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        vista_object = get_vista_object(self, super().get_queryset(), 'libtekin.item' )
        self.filter_object = vista_object['filter_object']
        self.order_by = vista_object['order_by']
        self.shown_fields = vista_object['shown_fields']
        self.common_text_search = vista_object['common_text_search']
        return vista_object['queryset']

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['mmodels'] = Mmodel.objects.all()
        context_data['mmodelcategories'] = MmodelCategory.objects.all()
        context_data['conditions'] = Condition.objects.all()
        context_data['roles'] = Role.objects.all()
        context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='libtekin.item').all()
        context_data['order_by_fields'] = self.order_by_fields
        context_data['order_by'] = self.order_by
        context_data['showable_fields'] = self.showable_fields
        context_data['shown_fields'] = self.shown_fields
        context_data['common_text_search'] = self.common_text_search

        if self.filter_object:
            context_data['filter_object'] = self.filter_object
        if self.request.POST.get('vista__name'):
            context_data['vista__name'] = self.request.POST.get('vista__name')

        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_item'
    model = Item
    template_name = 'libtekin/item_closer.html'

class MmodelCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_mmodel'
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        if 'opener' in self.request.POST and self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:mmodel-close', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('libtekin:mmodel-detail', kwargs={'pk': self.object.pk})

        return response

class MmodelUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_mmodel'
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        return reverse_lazy('libtekin:mmodel-detail', kwargs={'pk': self.object.pk})


class MmodelDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['mmodel_labels'] = { field.name: field.verbose_name.title() for field in Mmodel._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data


class MmodelDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'libtekin.delete_mmodel'
    model = Mmodel
    success_url = reverse_lazy('libtekin:mmodel-list')

class MmodelList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['mmodel_labels'] = { field.name: field.verbose_name.title() for field in Mmodel._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        return context_data

class MmodelClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel
    template_name = 'libtekin/mmodel_closer.html'

class MmodelCategoryCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_MmodelCategory'
    model = MmodelCategory
    form_class = MmodelCategoryForm

    def get_success_url(self):
        if 'opener' in self.request.POST and self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:mmodelcategory-close', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('libtekin:mmodelcategory-detail', kwargs={'pk': self.object.pk})

        return response

class MmodelCategoryUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_MmodelCategory'
    model = MmodelCategory
    form_class = MmodelCategoryForm

    def get_success_url(self):
        return reverse_lazy('libtekin:mmodelcategory-detail', kwargs={'pk': self.object.pk})

class MmodelCategoryDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_MmodelCategory'
    model = MmodelCategory

class MmodelCategoryDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'libtekin.delete_MmodelCategory'
    model = MmodelCategory
    success_url = reverse_lazy('libtekin:MmodelCategory-list')

class MmodelCategoryList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_MmodelCategory'
    model = MmodelCategory

class MmodelCategoryClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_MmodelCategory'
    model = MmodelCategory
    template_name = 'libtekin/MmodelCategory_closer.html'

class LocationCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_location'
    model = Location
    form_class = LocationForm

    def get_success_url(self):
        if 'opener' in self.request.POST and self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:location-close', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('libtekin:location-detail', kwargs={'pk': self.object.pk})

class LocationUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_location'
    model = Location
    form_class = LocationForm

    def get_success_url(self):
        return reverse_lazy('libtekin:location-detail', kwargs={'pk': self.object.pk})

class LocationDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_location'
    model = Location

class LocationDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'libtekin.delete_location'
    model = Location
    success_url = reverse_lazy('libtekin:location-list')

class LocationList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_location'
    model = Location

class LocationClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_location'
    model = Location
    template_name = 'libtekin/location_closer.html'

class EntityCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_entity'
    model = Entity
    form_class = EntityForm

    def get_success_url(self):
        if 'opener' in self.request.POST and self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:entity-close', kwargs={'pk': self.object.pk})
        else:
            return reverse_lazy('libtekin:entity-detail', kwargs={'pk': self.object.pk})

class EntityUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_entity'
    model = Entity
    form_class = EntityForm

    def get_success_url(self):
        return reverse_lazy('libtekin:entity-detail', kwargs={'pk': self.object.pk})


class EntityDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_entity'
    model = Entity

class EntityDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'libtekin.delete_entity'
    model = Entity
    success_url = reverse_lazy('libtekin:entity-list')

class EntityList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_entity'
    model = Entity

class EntityClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_entity'
    model = Entity
    template_name = 'libtekin/entity_closer.html'

def get_primary_id_field( request, mmodel_id):
    try:
        return Mmodel.objects.get(pk=mmodel_id).primary_id_field
    except ObjectDoesNotExist:
        return None

