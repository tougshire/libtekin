import json

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.core.exceptions import FieldError, ObjectDoesNotExist
from .forms import EntityForm, ItemForm, ItemNoteForm, ItemItemNoteFormSet, LocationForm, MmodelForm, MmodelCategoryForm
from .models import Condition, Entity, Item, ItemNote, Location, Mmodel, MmodelCategory, ViewItem, History

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
            context_data['itemnotes'] = ItemItemNoteFormSet(self.request.POST)
        else:
            context_data['itemnotes'] = ItemItemNoteFormSet()

        return context_data

    def form_valid(self, form):

        response = super().form_valid(form)

        update_history(form, 'Item', form.instance, self.request.user)

        self.object = form.save()

        itemnotes = ItemItemNoteFormSet(self.request.POST, instance=self.object)

        if itemnotes.is_valid():
            for form in itemnotes.forms:
                update_history(form, 'ItemNote', form.instance, self.request.user)

            itemnotes.save()
        else:
            print("formset is not not valid")
            print(itemnotes.errors)
            for form in itemnotes.forms:
                print( form.errors )

        return response

class ItemUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_item'
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.request.POST:
            context_data['itemnotes'] = ItemItemNoteFormSet(self.request.POST, instance=self.object)
        else:
            context_data['itemnotes'] = ItemItemNoteFormSet(instance=self.object)

        return context_data

    def form_valid(self, form):

        if 'copy' in self.request.POST:
            form.instance.pk=None

        update_history(form, 'Item', form.instance, self.request.user)

        response = super().form_valid(form)

        itemnotes = ItemItemNoteFormSet(self.request.POST, instance=self.object)

        if itemnotes.is_valid():

            for form in itemnotes.forms:
                update_history(form, 'Item', form.instance, self.request.user)

            itemnotes.save()
        else:
            print("formset is not not valid")
            print(itemnotes.errors)
            for form in itemnotes.forms:
                print( form.errors )




        return response

class ItemDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_item'
    model = Item

    def get_context_data(self, **kwargs):

        context_data = super().get_context_data(**kwargs)
        #context_data['current_notes'] = self.object.itemnote_set.all().filter(is_current_status=True)
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['itemnote_labels'] = { field.name: field.verbose_name.title() for field in ItemNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

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
        context_data['current_notes'] = self.object.itemnote_set.all().filter(is_current_status=True)
        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }
        context_data['itemnote_labels'] = { field.name: field.verbose_name.title() for field in ItemNote._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class ItemList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_item'
    model = Item
    filter_object = {}
    order_by = []
    order_by_fields=[]
    for fieldname in ['common_name', 'mmodel', 'primary_id', 'serial_number','service_number']:
        order_by_fields.append(
            { 'name':fieldname, 'label':Item._meta.get_field(fieldname).verbose_name.title() }
        )
        order_by_fields.append(
            { 'name':'-' + fieldname, 'label':'{} reverse'.format(Item._meta.get_field(fieldname).verbose_name.title()) }
        )

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):

        order_by = []
        filter_object={}

        if 'query_submitted' in self.request.POST:

            for i in range(0,3):
                order_by_i = 'order_by_{}'.format(i)
                if order_by_i in self.request.POST:
                    for field in self.order_by_fields:
                        if self.request.POST.get(order_by_i) == field['name']:
                            order_by.append(field['name'])

            for fieldname in ['mmodel', 'mmodel__mmodelcategory', 'condition']:
                filterfieldname = 'filter__' + fieldname + '__in'
                if filterfieldname in self.request.POST and self.request.POST.get(filterfieldname) > '':
                    postfields = self.request.POST.getlist(filterfieldname)
                    fieldlist = []
                    for postfield in postfields:
                        if postfield.isdecimal():
                            fieldlist.append(postfield)
                    if fieldlist:
                        filter_object[fieldname + '__in'] = postfields

            viewitem__name = ''
            if 'viewitem__name' in self.request.POST and self.request.POST.get('viewitem__name') > '':
                viewitem__name = self.request.POST.get('viewitem__name')

            if filter_object or order_by:

                queryset = super().get_queryset()

                viewitem, created = ViewItem.objects.get_or_create( user=self.request.user, name=viewitem__name )

                if filter_object:
                    self.filter_object = filter_object
                    viewitem.filterstring = json.dumps( filter_object )
                    queryset = queryset.filter(**filter_object)

                if order_by:
                    self.order_by = order_by
                    viewitem.sortstring = ','.join(order_by)
                    queryset = queryset.order_by(*order_by)

                viewitem.save()

                return queryset

        elif 'get_viewitem' in self.request.POST:

            viewitem__name = ''

            if 'viewitem__name' in self.request.POST and self.request.POST.get('viewitem__name') > '':
                viewitem__name = self.request.POST.get('viewitem__name')

            viewitem, created = ViewItem.objects.get_or_create( user=self.request.user, name=viewitem__name )

            try:
                filter_object = json.loads(viewitem.filterstring)
                order_by = viewitem.sortstring.split(',')
                queryset = super().get_queryset().filter(**filter_object).order_by(*order_by)
                self.filter_object = filter_object

                return queryset

            except json.JSONDecodeError:
                pass

        elif 'delete_viewitem' in self.request.POST:

            viewitem__name = ''

            if 'viewitem__name' in self.request.POST and self.request.POST.get('viewitem__name') > '':

                viewitem__name = self.request.POST.get('viewitem__name')
                ViewItem.objects.filter( user=self.request.user, name=viewitem__name ).delete()


        # this code runs if no queryset has been returned yet
            viewitem = ViewItem.objects.filter( user=self.request.user, is_default=True ).last()
            if viewitem is None:
                viewitem = ViewItem.objects.filter( user=self.request.user ).last()
            if viewitem is None:
                viewitem, created = ViewItem.objects.get_or_create( user=self.request.user )

            try:
                filter_object = json.loads(viewitem.filterstring)
                order_by = viewitem.sortstring.split(',')
                try:
                    self.filter_object = filter_object
                    self.order_by = order_by

                    return super().get_queryset().filter(**filter_object).order_by(order_by)

                except (ValueError, TypeError, FieldError):
                    print('Field/Value/Type Error')
                    viewitem.delete()

            except json.JSONDecodeError:
                print('deserialization error')
                viewitem.delete()

        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['mmodels'] = Mmodel.objects.all()
        context_data['mmodelcategories'] = MmodelCategory.objects.all()
        context_data['conditions'] = Condition.objects.all()
        context_data['viewitems'] = ViewItem.objects.filter(user=self.request.user).all()
        context_data['order_by_fields'] = self.order_by_fields

        for i in range(0,3):
            try:
                context_data['order_by_{}'.format(i)] = self.order_by[i]
            except IndexError:
                pass

        if self.filter_object:
            context_data['filter_object'] = self.filter_object
        if self.request.POST.get('viewitem__name'):
            context_data['viewitem__name'] = self.request.POST.get('viewitem__name')

#        context_data['item_labels'] = {}
#        for fieldname in ['common_name', 'mmodel']:
#            context_data['item_labels'][fieldname] = Item._meta.get_field("common_name").verbose_name.capitalize()

        context_data['item_labels'] = { field.name: field.verbose_name.title() for field in Item._meta.get_fields() if type(field).__name__[-3:] != 'Rel' }

        return context_data

class MmodelCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_mmodel'
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        if self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:mmodel_close', kwargs={'pk': self.object.pk})
        else:
            return super().get_success_url()

        return response

class MmodelUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_mmodel'
    model = Mmodel
    form_class = MmodelForm

class MmodelDetail(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel

class MmodelDelete(PermissionRequiredMixin, DeleteView):
    permission_required = 'libtekin.delete_mmodel'
    model = Mmodel
    success_url = reverse_lazy('libtekin:mmodel-list')

class MmodelList(PermissionRequiredMixin, ListView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel

class MmodelClose(PermissionRequiredMixin, DetailView):
    permission_required = 'libtekin.view_mmodel'
    model = Mmodel
    template_name = 'libtekin/mmodel_closer.html'

class MmodelCategoryCreate(PermissionRequiredMixin, CreateView):
    permission_required = 'libtekin.add_MmodelCategory'
    model = MmodelCategory
    form_class = MmodelCategoryForm

    def get_success_url(self):
        if self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:mmodelcategory_close', kwargs={'pk': self.object.pk})
        else:
            return super().get_success_url()

        return response

class MmodelCategoryUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_MmodelCategory'
    model = MmodelCategory
    form_class = MmodelCategoryForm

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
        if self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:location_close', kwargs={'pk': self.object.pk})
        else:
            return super().get_success_url()

        return response

class LocationUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_location'
    model = Location
    form_class = LocationForm

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
        if self.request.POST['opener'] > '':
            return reverse_lazy('libtekin:entity_close', kwargs={'pk': self.object.pk})
        else:
            return super().get_success_url()

        return response

class EntityUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = 'libtekin.change_entity'
    model = Entity
    form_class = EntityForm

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

