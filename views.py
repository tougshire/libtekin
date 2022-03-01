import json, sys

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from django.views.generic.list import ListView
from tougshire_vistas.models import Vista
from tougshire_vistas.views import make_vista, retrieve_vista, get_latest_vista, delete_vista, get_global_vista

from .forms import (EntityForm, ItemForm, ItemItemNoteFormset, LocationForm,
                    MmodelCategoryForm, MmodelForm, ItemCopyForm)
from .models import (Condition, Entity, History, Item, ItemNote, Location,
                     Mmodel, MmodelCategory, Role)


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

def xcopy_item(request, pk, qty=1):
    item = Item.objects.get(pk=pk)
    item.pk=None
    item.common_name = '[copy of] ' + item.common_name
    item.save() # item is now a new item, the original item is untouched
    return HttpResponseRedirect(reverse('libtekin:item-update', kwargs={'pk':item.pk}))

class ItemCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_item'
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        if self.request.POST:
            context_data['itemnotes'] = ItemItemNoteFormset(self.request.POST)
        else:
            context_data['itemnotes'] = ItemItemNoteFormset()

        return context_data

    def form_valid(self, form):

        response = super().form_valid(form)

        update_history(form, 'Item', form.instance, self.request.user)

        self.object = form.save()

        if self.request.POST:
            itemnotes = ItemItemNoteFormset(self.request.POST, instance=self.object)
        else:
            itemnotes = ItemItemNoteFormset(instance=self.object)

        if(itemnotes).is_valid():
            itemnotes.save()
        else:
            return self.form_invalid(form)


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
            context_data['itemnotes'] = ItemItemNoteFormset(self.request.POST, instance=self.object)
        else:
            context_data['itemnotes'] = ItemItemNoteFormset(instance=self.object)

        return context_data

    def form_valid(self, form):

        update_history(form, 'Item', form.instance, self.request.user)

        response = super().form_valid(form)

        self.object = form.save()

        if self.request.POST:
            itemnotes = ItemItemNoteFormset(self.request.POST, instance=self.object)
        else:
            itemnotes = ItemItemNoteFormset(instance=self.object)

        if(itemnotes).is_valid():
            itemnotes.save()
        else:
            return self.form_invalid(form)

        return response

    def get_success_url(self):
        return reverse_lazy('libtekin:item-detail', kwargs={ 'pk':self.object.pk })


class ItemDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_item'
    model = Item

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['itemnote_labels'] = { field.name: field.verbose_name.title() for field in ItemNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemCopy(DetailView, FormView):
    permission_required = 'libtekin.add_item'
    template_name='libtekin/item_confirm_copy.html'
    form_class = ItemCopyForm
    model = Item

    def form_valid(self, form):

        item = Item.objects.get(pk=self.kwargs.get('pk'))
        qty = form.cleaned_data['qty']
        print('m31a59', qty)
        primary_id = item.primary_id
        for n in range(0,qty):
            print('m31b00')
            item.pk=None
            item.primary_id = '[copy of] ' + primary_id
            setattr(item, item.primary_id_field, '[copy of] ' + primary_id)
            item.save() # item is now a new item, the original item is untouched

        return redirect(reverse_lazy('libtekin:item-list-by', kwargs={'fieldname':'primary_id', 'fieldvalue':primary_id} ))


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
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['itemnote_labels'] = { field.name: field.verbose_name.title() for field in ItemNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_item'
    model = Item
    paginate_by = 30

    def setup(self, request, *args, **kwargs):

        self.vista_settings={
            'text_fields_available':[],
            'filter_fields_available':{},
            'order_by_fields_available':[],
            'columns_available':[]
        }

        self.vista_settings['text_fields_available']=[
            'common_name',
            'mmodel__model_name',
            'mmodel__category__name',
            'mmodel__brand',
            'primary_id',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'phone_number',
            'essid',
            'network_name',
            'assignee__friendly_name',
            'assignee__full_name',
            'borrower__friendly_name',
            'borrower__full_name',
            'owner__friendly_name',
            'owner__full_name',
            'home__short_name',
            'home__full_name',
            'location__short_name',
            'location__full_name',
        ]

        self.vista_settings['filter_fields_available'] = [
            'mmodel',
            'mmodel__category',
            'condition',
            'role',
            'location',
            'home',
            'latest_inventory',
            'primary_id',
        ]

        for fieldname in [
            'common_name',
            'mmodel',
            'primary_id',
            'serial_number',
            'service_number',
            'latest_inventory'
        ]:
            self.vista_settings['order_by_fields_available'].append(fieldname)
            self.vista_settings['order_by_fields_available'].append('-' + fieldname)


        for fieldname in [
            'common_name',
            'mmodel',
            'primary_id_field',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'phone_number',
            'essid',
            'condition',
            'network_name',
            'assignee',
            'owner',
            'borrower',
            'home',
            'location',
            'role',
            'latest_inventory'
        ]:
            self.vista_settings['columns_available'].append(fieldname)

        self.vista_defaults = {
            'order_by': Item._meta.ordering,
            'paginate_by':self.paginate_by
        }

        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):

        print('tp m2sj26')
        print(self.kwargs)
        print(kwargs)

        self.vista_context = {
            'show_columns':[],
            'order_by':[],
            'combined_text_search':'',
        }

        queryset = super().get_queryset()

        vistaobj={'context':{}, 'queryset':queryset}

        if 'delete_vista' in self.request.POST:
            delete_vista(self.request)

        if 'fieldname' in self.kwargs and 'fieldvalue' in self.kwargs:
            if self.kwargs['fieldname'] in self.vista_settings['text_fields_available']:
                vistaobj = make_vista(self.request, self.vista_settings, super().get_queryset(), { 'filterfield__' + self.kwargs['fieldname']:self.kwargs['fieldvalue'], 'filterop__' + self.kwargs['fieldname']: 'contains' })
        else:
            if 'vista_query_submitted' in self.request.POST:
                vistaobj = make_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
            elif 'retrieve_vista' in self.request.POST:
                vistaobj = retrieve_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
            else:
                try:
                    vistaobj =  get_latest_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
                except Vista.DoesNotExist as e:
                    print(type(e), e, ' at ', sys.exc_info()[2].tb_lineno)
                    try:
                        vistaobj =  get_global_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)
                    except Vista.DoesNotExist as e:
                        print(type(e), e, ' at ', sys.exc_info()[2].tb_lineno)
                        vistaobj = make_vista(self.request, self.vista_settings, super().get_queryset(), self.vista_defaults)


        for key in vistaobj['context']:
            self.vista_context[key] = vistaobj['context'][key]

        queryset = vistaobj['queryset']

        return queryset

    def get_paginate_by(self, queryset):

        if 'paginate_by' in self.vista_context and self.vista_context['paginate_by']:
            return self.vista_context['paginate_by']

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        context_data['mmodels'] = Mmodel.objects.all()
        context_data['mmodelcategories'] = MmodelCategory.objects.all()
        context_data['conditions'] = Condition.objects.all()
        context_data['roles'] = Role.objects.all()
        context_data['locations'] = Location.objects.all()

        context_data['order_by_fields_available'] = []
        for fieldname in self.vista_settings['order_by_fields_available']:
            if fieldname > '' and fieldname[0] == '-':
                context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':Item._meta.get_field(fieldname[1:]).verbose_name.title() + ' [Reverse]'})
            else:
                context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title()})

        context_data['columns_available'] = [{ 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title() } for fieldname in self.vista_settings['columns_available']]

        context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='libtekin.item').all()

        if self.request.POST.get('vista__name'):
            context_data['vista__name'] = self.request.POST.get('vista__name')

        if self.vista_context:
            if 'filter' in self.vista_context:
                for key in self.vista_context['filter']:
                    context_data[key] = self.vista_context['filter'][key]

        for key in [
            'combined_text_search',
            'text_fields_chosen',
            'order_by',
            'paginate_by'
            ]:
            if key in self.vista_context and self.vista_context[key]:
                context_data[key] = self.vista_context[key]

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

