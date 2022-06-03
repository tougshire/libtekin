import sys
import urllib
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.http import QueryDict
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormView,
                                       UpdateView)
from django.views.generic.list import ListView
from tougshire_vistas.models import Vista
from tougshire_vistas.views import (default_vista, delete_vista,
                                    get_global_vista, get_latest_vista,
                                    make_vista, make_vista_fields,
                                    retrieve_vista, vista_context_data)

from .forms import (EntityForm, ItemCopyForm, ItemForm, ItemItemNoteFormset,
                    LocationForm, MmodelCategoryForm, MmodelForm)
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
        primary_id = item.primary_id
        for n in range(0,qty):
            item.pk=None
            item.primary_id = '[copy of] ' + primary_id
            setattr(item, item.primary_id_field, '[copy of] ' + primary_id)
            item.save() # item is now a new item, the original item is untouched

        self.request.session['query']='filter__fieldname__0=primary_id&filter__op__0=contains&filter__value__0=[copy of] ' + primary_id

        return redirect('libtekin:item-list')



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
            'max_search_keys':5,
            'fields':[],
        }

        self.vista_settings['fields'] = make_vista_fields(Item, field_names=[
            'primary_id',
            'common_name',
            'mmodel',
            'network_name',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'phone_number',
            'role',
            'connected_to',
            'essid',
            'owner',
            'assignee',
            'borrower',
            'home',
            'location',
            'status',
            'connected_to__mmodel',
            'connection__mmodel',
            'latest_inventory',
            'installation_date',
            'status__is_active',
            'itemnote__is_current',
        ])

        self.vista_settings['fields']['itemnote__is_current']['label'] = "Has Current Notes"


        self.vista_defaults = QueryDict(urlencode([
            ('filter__fieldname__0', ['status__is_active']),
            ('filter__op__0', ['exact']),
            ('filter__value__0', [True]),
            ('order_by', ['primary_id', 'common_name']),
            ('paginate_by',self.paginate_by),
        ],doseq=True) )

        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):

        queryset = super().get_queryset()

        self.vistaobj = {'querydict':QueryDict(), 'queryset':queryset}

        if 'delete_vista' in self.request.POST:
            delete_vista(self.request)

        if 'query' in self.request.session:
            print('tp 224bc49', 'query in self.request.session')
            querydict = QueryDict(self.request.session.get('query'))
            self.vistaobj = make_vista(
                self.request.user,
                queryset,
                querydict,
                '',
                False,
                self.vista_settings
            )
            del self.request.session['query']

        elif 'vista_query_submitted' in self.request.POST:
            print('tp 224bc50', 'vista_query_submitted')

            self.vistaobj = make_vista(
                self.request.user,
                queryset,
                self.request.POST,
                self.request.POST.get('vista_name') if 'vista_name' in self.request.POST else '',
                self.request.POST.get('make_default') if ('make_default') in self.request.POST else False,
                self.vista_settings
            )
        elif 'retrieve_vista' in self.request.POST:
            print('tp 224bc51', 'retrieve_vista')

            self.vistaobj = retrieve_vista(
                self.request.user,
                queryset,
                'libtekin.item',
                self.request.POST.get('vista_name'),
                self.vista_settings

            )
        elif 'default_vista' in self.request.POST:
            print('tp 224bc52', 'default_vista')

            self.vistaobj = default_vista(
                self.request.user,
                queryset,
                self.vista_defaults,
                self.vista_settings
            )
        else:
            self.vistaobj = get_latest_vista(
                self.request.user,
                queryset,
                self.vista_defaults,
                self.vista_settings
            )

            print('tp 224bc53', 'else')

        return self.vistaobj['queryset']

    def get_paginate_by(self, queryset):

        if 'paginate_by' in self.vistaobj['querydict'] and self.vistaobj['querydict']['paginate_by']:
            return self.vistaobj['querydict']['paginate_by']

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        vista_data = vista_context_data(self.vista_settings, self.vistaobj['querydict'])

        context_data = {**context_data, **vista_data}

        context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='libtekin.item').all() # for choosing saved vistas

        if self.request.POST.get('vista_name'):
            context_data['vista_name'] = self.request.POST.get('vista_name')

        context_data['count'] = self.object_list.count()

        return context_data


class ItemCSV(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_item'
    model = Item
    template_name = 'libtekin/item_csv.html'
    content_type='text/csv'

    def setup(self, request, *args, **kwargs):

        self.vista_settings={
            'max_search_keys':5,
            'fields':[],
        }

        self.vista_settings['fields'] = make_vista_fields(Item, field_names=[
            'primary_id',
            'common_name',
            'mmodel',
            'network_name',
            'serial_number',
            'service_number',
            'asset_number',
            'barcode',
            'phone_number',
            'role',
            'connected_to',
            'essid',
            'owner',
            'assignee',
            'borrower',
            'home',
            'location',
            'status',
            'connected_to__mmodel',
            'connection__mmodel',
            'latest_inventory',
            'installation_date',
            'status__is_active',
            'itemnote__is_current',
        ])

        self.vista_settings['fields']['itemnote__is_current']['label'] = "Has Current Notes"


        self.vista_defaults = QueryDict(urlencode([
            ('filter__fieldname__0', ['status__is_active']),
            ('filter__op__0', ['exact']),
            ('filter__value__0', [True]),
            ('order_by', ['primary_id', 'common_name']),
            ('paginate_by',self.paginate_by),
        ],doseq=True) )

        return super().setup(request, *args, **kwargs)

    def get_queryset(self, **kwargs):

        queryset = super().get_queryset()

        self.vistaobj = {'querydict':QueryDict(), 'queryset':queryset}

        self.vistaobj = get_latest_vista(
            self.request.user,
            queryset,
            self.vista_defaults,
            self.vista_settings
        )

        return self.vistaobj['queryset']

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        vista_data = vista_context_data(self.vista_settings, self.vistaobj['querydict'])

        context_data = {**context_data, **vista_data}

        context_data['count'] = self.object_list.count()

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

