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
                                    make_vista, retrieve_vista)

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
        print('m31a59', qty)
        primary_id = item.primary_id
        for n in range(0,qty):
            print('m31b00')
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
            'max_search_keys':10,
            'text_fields_available':[],
            'filter_fields_available':{},
            'order_by_fields_available':[],
            'columns_available':[]
        }

        self.vista_fields = {

            'asset_number':{
                'label':'Asset Number',
				'type':'char',
				'available_for':[
					'quicksearch',
					'fieldsearch',
                    'order_by',
                    'columns',
				]
            },
            'assignee':{
                'label':'Assigned To',
                'type':'model',
                'source':Entity.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'assignee__friendly_name':{
                'label':'Assignee Friendly Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'assignee__full_name':{
                'label':'Assignee Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'barcode':{
                'label':'Barcode',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'borrower':{
                'label':'Borrowed By',
                'type':'model',
                'source':Entity.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'borrower__friendly_name':{
                'label':'Borrower Friendly Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'borrower__full_name':{
                'label':'Borrower Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'common_name':{
                'label':'Common Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'condition':{
                'label':'Condition',
                'type':'model',
                'source':Condition.objects.all(),
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'connected_to':{
                'label':'Connected To',
                'type':'model',
                'source':Item.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'connected_to__mmodel':{
                'label':'Connected To Model',
                'type':'model',
                'source':Mmodel.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'columns'
                ]
            },
            'essid':{
                'label':'ESSID',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'home':{
                'label':'Home',
                'type':'model',
                'source':Location.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'home__full_name':{
                'label':'Home Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'home__short_name':{
                'label':'Home Short Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'itemnote__text':{
                'label':'Note',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'columns'
                ]
            },
            'latest_inventory':{
                'label':'Latest Inventory',
                'type':'date',
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'location':{
                'label':'Current Location',
                'type':'model',
                'source':Location.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'location__full_name':{
                'label':'Location Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]

            },
            'location__short_name':{
                'label':'Location Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'mmodel':{
                'label':'Model',
                'source':Mmodel.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'mmodel__brand':{
                'label':'Brand',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'mmodel__category':{
                'label':'Category',
                'type':'model',
                'source':MmodelCategory.objects.all(),
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'mmodel__category__name':{
                'label':'Category Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'mmodel__model_name':{
                'label':'Model Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'network_name':{
                'label':'Network Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'owner':{
                'label':'Owner',
                'type':'model',
                'source':Entity.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'owner__friendly_name':{
                'label':'Owner Friendly Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'owner__full_name':{
                'label':'Owner Full Name',
                'type':'char',
                'available_for':[
                    'quicksearch',
                ]
            },
            'phone_number':{
                'label':'Phone Number',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'primary_id':{
                'label':'Primar Id',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'role':{
                'label':'Role',
                'source':Role.objects.all(),
                'available_for':[
                    'fieldsearch',
                    'order_by',
                    'columns',
                ]
            },
            'serial_number':{
                'label':'Serial Number',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'service_number':{
                'label':'Service Number',
                'type':'char',
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            },
            'status':{
                'label':'Status',
                'type':'choice',
                'source':Item.STATUS_CHOICES,
                'available_for':[
                    'quicksearch',
                    'fieldsearch',
                    'order_by',
                    'columns'
                ]
            }
        }

        self.field_labels =  {  key:value['label']  for ( key, value ) in self.vista_fields.items() if 'label' in value  }

        self.vista_settings['field_types'] =  {  key:value['type']  for ( key, value ) in self.vista_fields.items() if 'type' in value  }

        self.vista_settings['text_fields_available'] = {  key  for ( key, value )  in self.vista_fields.items() if 'available_for' in value and 'quicksearch' in value['available_for']  }

        self.vista_settings['filter_fields_available'] = {  key  for ( key, value )  in self.vista_fields.items() if 'available_for' in value and 'fieldsearch' in value['available_for']  }

        self.vista_settings['order_by_fields_available'] = [  key  for ( key, value )  in self.vista_fields.items() if 'available_for' in value and 'order_by' in value['available_for']  ]

        self.vista_settings['order_by_fields_available'] = self.vista_settings['order_by_fields_available'] + [  '-' + key  for ( key, value )  in self.vista_fields.items() if 'available_for' in value and 'order_by' in value['available_for']  ]

        self.vista_settings['columns_available'] = {  key  for ( key, value )  in self.vista_fields.items() if 'available_for' in value and 'columns' in value['available_for']  }


        self.vista_defaults = QueryDict(urlencode([
            ('filter__fieldname', ['status']),
            ('filter__op', ['in']),
            ('filter__value', [1]),
            ('order_by', ['priority', 'begin']),
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

            self.vistaobj = make_vista(
                self.request.user,
                queryset,
                self.request.POST,
                self.request.POST.get('vista_name') if 'vista_name' in self.request.POST else '',
                self.request.POST.get('make_default') if ('make_default') in self.request.POST else False,
                self.vista_settings
            )
        elif 'retrieve_vista' in self.request.POST:
            self.vistaobj = retrieve_vista(
                self.request.user,
                queryset,
                'libtekin.item',
                self.request.POST.get('vista_name'),
                self.vista_settings

            )
        elif 'default_vista' in self.request.POST:

            self.vistaobj = default_vista(
                self.request.user,
                queryset,
                self.vista_defaults,
                self.vista_settings
            )

        return self.vistaobj['queryset']

    def get_paginate_by(self, queryset):

        if 'paginate_by' in self.vistaobj['querydict'] and self.vistaobj['querydict']['paginate_by']:
            return self.vistaobj['querydict']['paginate_by']

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)

        context_data['order_by_fields_available'] = []
        for fieldname in self.vista_settings['order_by_fields_available']:
            if fieldname > '' and fieldname[0] == '-':
                context_data['order_by_fields_available'].append({ 'name':fieldname[1:], 'label':self.field_labels[fieldname[1:]] + ' [Reverse]'})
            else:
                context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':self.field_labels[fieldname]})

        context_data['columns_available'] = [{ 'name':key, 'label':value['label'] } for key, value in self.vista_fields.items() if 'columns' in value['available_for'] ]

        context_data['filter_fields_available'] = [{ 'name':fieldname, 'label':self.vista_fields[fieldname]['label'], 'options':{'type':self.vista_fields[fieldname]['type'] if 'type' in self.vista_fields[fieldname] else '', 'values':self.vista_fields[fieldname]['source'] if 'source' in self.vista_fields[fieldname] else ''} } for fieldname in self.vista_settings['filter_fields_available']]

        context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='sdcpeople.person').all() # for choosing saved vistas

        if self.request.POST.get('vista_name'):
            context_data['vista_name'] = self.request.POST.get('vista_name')

        vista_querydict = self.vistaobj['querydict']

        #putting the index before person name to make it easier for the template to iterate
        context_data['filter'] = []
        for indx in range( self.vista_settings['max_search_keys']):
            cdfilter = {}
            cdfilter['fieldname'] = vista_querydict.get('filter__fieldname__' + str(indx)) if 'filter__fieldname__' + str(indx) in vista_querydict else ''
            cdfilter['op'] = vista_querydict.get('filter__op__' + str(indx) ) if 'filter__op__' + str(indx) in vista_querydict else ''
            cdfilter['value'] = vista_querydict.get('filter__value__' + str(indx)) if 'filter__value__' + str(indx) in vista_querydict else ''
            if cdfilter['op'] in ['in', 'range']:
                cdfilter['value'] = vista_querydict.getlist('filter__value__' + str(indx)) if 'filter__value__'  + str(indx) in vista_querydict else []
            context_data['filter'].append(cdfilter)

        context_data['order_by'] = vista_querydict.getlist('order_by') if 'order_by' in vista_querydict else Item._meta.ordering

        context_data['combined_text_search'] = vista_querydict.get('combined_text_search') if 'combined_text_search' in vista_querydict else ''

        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        # context_data = super().get_context_data(**kwargs)

        # context_data['mmodels'] = Mmodel.objects.all()
        # context_data['mmodelcategories'] = MmodelCategory.objects.all()
        # context_data['conditions'] = Condition.objects.all()
        # context_data['status']=Item.STATUS_CHOICES
        # context_data['roles'] = Role.objects.all()
        # context_data['locations'] = Location.objects.all()
        # context_data['entities'] = Entity.objects.all()

        # context_data['order_by_fields_available'] = []
        # for fieldname in self.vista_settings['order_by_fields_available']:
        #     if fieldname > '' and fieldname[0] == '-':
        #         context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':Item._meta.get_field(fieldname[1:]).verbose_name.title() + ' [Reverse]'})
        #     else:
        #         context_data['order_by_fields_available'].append({ 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title()})

        # context_data['columns_available'] = [{ 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title() } for fieldname in self.vista_settings['columns_available']]

        # context_data['vistas'] = Vista.objects.filter(user=self.request.user, model_name='libtekin.item').all() # for choosing saved vistas

        # if self.request.POST.get('vista_name'):
        #     context_data['vista_name'] = self.request.POST.get('vista_name')

        # vista_querydict = self.vistaobj['querydict']
        # print('tp m3b324', vista_querydict)

        # #putting the index before item name to make it easier for the template to iterate
        # context_data['filter'] = []
        # for indx in range( self.vista_settings['max_search_keys']):
        #     cdfilter = {}
        #     cdfilter['fieldname'] = vista_querydict.get('filter__fieldname__' + str(indx)) if 'filter__fieldname__' + str(indx) in vista_querydict else ''
        #     cdfilter['op'] = vista_querydict.get('filter__op__' + str(indx) ) if 'filter__op__' + str(indx) in vista_querydict else ''
        #     cdfilter['value'] = vista_querydict.get('filter__value__' + str(indx)) if 'filter__value__' + str(indx) in vista_querydict else ''
        #     if cdfilter['op'] in ['in', 'range']:
        #         cdfilter['value'] = vista_querydict.getlist('filter__value__' + str(indx)) if 'filter__value__'  + str(indx) in vista_querydict else []
        #     context_data['filter'].append(cdfilter)

        # context_data['order_by'] = vista_querydict.getlist('order_by') if 'order_by' in vista_querydict else Item._meta.ordering

        # context_data['combined_text_search'] = vista_querydict.get('combined_text_search') if 'combined_text_search' in vista_querydict else ''

        # context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

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

