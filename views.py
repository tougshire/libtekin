import csv
import logging
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.db.models import Q
from django.http import QueryDict
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from django_filters_stoex.forms import (
    FilterstoreRetrieveForm,
    FilterstoreSaveForm,
)
from django_filters_stoex.views import FilterView
from libtekin.filterset import ItemFilter
from spl_members.models import Member

from .forms import (
    EntityForm,
    ItemAssigneeFormset,
    ItemBorrowerFormset,
    ItemCopyForm,
    ItemForm,
    ItemItemNoteFormset,
    ItemNoteCategoryForm,
    ItemNoteForm,
    LocationForm,
    MmodelCategoryForm,
    MmodelForm,
    CSVOptionForm,
    MemberForm,
)
from .models import (
    Entity,
    History,
    Item,
    ItemNote,
    ItemNoteCategory,
    ItemNoteLevel,
    Location,
    Mmodel,
    MmodelCategory,
    Role,
)

logger = logging.getLogger(__name__)


def update_history(form, modelname, object, user):
    for fieldname in form.changed_data:
        try:
            old_value = (str(form.initial[fieldname]),)
        except KeyError:
            old_value = None

        history = History.objects.create(
            user=user,
            modelname=modelname,
            objectid=object.pk,
            fieldname=fieldname,
            old_value=old_value,
            new_value=str(form.cleaned_data[fieldname]),
        )

        history.save()


class ItemCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_item"
    model = Item
    form_class = ItemForm
    template_name = "libtekin/item_create.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemassignees": ItemAssigneeFormset,
        }

        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                context_data[formsetkey] = formsetclass(self.request.POST)
            else:
                context_data[formsetkey] = formsetclass()

        return context_data

    def form_valid(self, form):
        response = super().form_valid(form)

        update_history(form, "Item", form.instance, self.request.user)

        self.object = form.save(commit=False)

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemAssignees": ItemAssigneeFormset,
        }
        formsetdata = {}
        formsets_valid = True
        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                formsetdata[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )
            else:
                formsetdata[formsetkey] = formsetclass(instance=self.object)

            if (formsetdata[formsetkey]).is_valid():
                formsetdata[formsetkey].save()
            else:
                logger.critical(formsetdata[formsetkey].errors)
                formsets_valid = False

        if not formsets_valid:
            return self.form_invalid(form)

        return response

    def get_success_url(self):

        if "popup" in self.request.get_full_path():
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "app_name": self.model._meta.app_label,
                    "model_name": self.model.__name__,
                },
            )
        return reverse_lazy("libtekin:item-detail", kwargs={"pk": self.object.pk})


class ItemCopy(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.add_item"
    model = Item
    fields = []
    template_name = "libtekin/item_copy.html"

    def form_valid(self, form):
        valid = super().form_valid(form)

        self.object = form.save(commit=False)

        self.object.pk = None
        self.object.common_name = "[Copy of] " + self.object.common_name
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("libtekin:item-update", kwargs={"pk": self.object.pk})


class ItemUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_item"
    model = Item
    form_class = ItemForm
    template_name = "libtekin/item_update.html"

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemassignees": ItemAssigneeFormset,
        }

        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                context_data[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )
            else:
                context_data[formsetkey] = formsetclass(instance=self.object)

        return context_data

    def form_valid(self, form):
        response = super().form_valid(form)

        self.object = form.save(commit=False)

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemAssignees": ItemAssigneeFormset,
        }
        formsetdata = {}
        formsets_valid = True
        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                formsetdata[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )

            else:
                formsetdata[formsetkey] = formsetclass(instance=self.object)

            if (formsetdata[formsetkey]).is_valid():
                formsetdata[formsetkey].save()
            else:
                logger.critical(formsetdata[formsetkey].errors)
                formsets_valid = False

        if not formsets_valid:
            return self.form_invalid(form)

        return response

        #############

        response = super().form_valid(form)

        update_history(form, "Item", form.instance, self.request.user)

        self.object = form.save()

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemAssignees": ItemAssigneeFormset,
        }
        formsetdata = {}
        formsets_valid = True
        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                formsetdata[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )
            else:
                formsetdata[formsetkey] = formsetclass(instance=self.object)

            if (formsetdata[formsetkey]).is_valid():
                formsetdata[formsetkey].save()
            else:
                logger.critical(formsetdata[formsetkey].errors)
                formsets_valid = False

        if not formsets_valid:
            return self.form_invalid(form)

        return response

    def get_success_url(self):
        if "popup" in self.kwargs:
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "app_name": "libtekin",
                    "model_name": "Item",
                },
            )
        return reverse_lazy("libtekin:item-detail", kwargs={"pk": self.object.pk})


class ItemDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_item"
    model = Item

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["item_labels"] = {
            field.name: field.verbose_name.title()
            for field in Item._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        context_data["itemnote_labels"] = {
            field.name: field.verbose_name.title()
            for field in ItemNote._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class ItemDelete(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.delete_item"
    model = Item
    success_url = reverse_lazy("libtekin:item-list")


class ItemSoftDelete(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.delete_item"
    model = Item
    template_name = "libtekin/item_confirm_delete.html"
    success_url = reverse_lazy("libtekin:item-list")
    fields = ["is_deleted"]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["item_labels"] = {
            field.name: field.verbose_name.title()
            for field in Item._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        context_data["itemnote_labels"] = {
            field.name: field.verbose_name.title()
            for field in ItemNote._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class ItemList(PermissionRequiredMixin, FilterView):
    permission_required = "libtekin.view_item"
    filterset_class = ItemFilter
    filterstore_urlname = "libtekin:item-filterstore"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["filterstore_retrieve"] = FilterstoreRetrieveForm()
        context_data["filterstore_save"] = FilterstoreSaveForm()
        context_data["as_csv"] = CSVOptionForm()
        context_data["count"] = self.object_list.count()
        context_data["labels"] = {
            field.name: field.verbose_name
            for field in Item._meta.get_fields()
            if hasattr(field, "verbose_name")
        }
        return context_data


class ItemClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_item"
    model = Item
    template_name = "libtekin/item_closer.html"


class MmodelCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_mmodel"
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        if "popup" in self.request.get_full_path():
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "model_name": self.model.__name__,
                    "app_name": self.model._meta.app_label,
                },
            )
        return reverse_lazy("libtekin:item-detail", kwargs={"pk": self.object.pk})


class MmodelUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_mmodel"
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        return reverse_lazy("libtekin:mmodel-detail", kwargs={"pk": self.object.pk})


class MmodelDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_mmodel"
    model = Mmodel

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["mmodel_labels"] = {
            field.name: field.verbose_name.title()
            for field in Mmodel._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class MmodelDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "libtekin.delete_mmodel"
    model = Mmodel
    success_url = reverse_lazy("libtekin:mmodel-list")


class MmodelList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_mmodel"
    model = Mmodel

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["mmodel_labels"] = {
            field.name: field.verbose_name.title()
            for field in Mmodel._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        return context_data


class MmodelClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_mmodel"
    model = Mmodel
    template_name = "libtekin/mmodel_closer.html"


class MmodelCategoryCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_MmodelCategory"
    model = MmodelCategory
    form_class = MmodelCategoryForm

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy(
                "libtekin:mmodelcategory-close", kwargs={"pk": self.object.pk}
            )
        else:
            return reverse_lazy(
                "libtekin:mmodelcategory-detail", kwargs={"pk": self.object.pk}
            )

        return response


class MmodelCategoryUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_MmodelCategory"
    model = MmodelCategory
    form_class = MmodelCategoryForm

    def get_success_url(self):
        return reverse_lazy(
            "libtekin:mmodelcategory-detail", kwargs={"pk": self.object.pk}
        )


class MmodelCategoryDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_MmodelCategory"
    model = MmodelCategory


class MmodelCategoryDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "libtekin.delete_MmodelCategory"
    model = MmodelCategory
    success_url = reverse_lazy("libtekin:MmodelCategory-list")


class MmodelCategoryList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_MmodelCategory"
    model = MmodelCategory


class MmodelCategoryClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_MmodelCategory"
    model = MmodelCategory
    template_name = "libtekin/MmodelCategory_closer.html"


class LocationCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_location"
    model = Location
    form_class = LocationForm

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy(
                "libtekin:location-close", kwargs={"pk": self.object.pk}
            )
        else:
            return reverse_lazy(
                "libtekin:location-detail", kwargs={"pk": self.object.pk}
            )


class LocationUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_location"
    model = Location
    form_class = LocationForm

    def get_success_url(self):
        return reverse_lazy("libtekin:location-detail", kwargs={"pk": self.object.pk})


class LocationDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_location"
    model = Location


class LocationDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "libtekin.delete_location"
    model = Location
    success_url = reverse_lazy("libtekin:location-list")


class LocationList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_location"
    model = Location


class LocationClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_location"
    model = Location
    template_name = "libtekin/location_closer.html"


class EntityCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_entity"
    model = Entity
    form_class = EntityForm

    def get_success_url(self):
        if "popup" in self.kwargs:
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "app_name": "libtekin",
                    "model_name": "Entity",
                },
            )
        return reverse_lazy("libtekin:entity-detail", kwargs={"pk": self.object.pk})


class EntityUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_entity"
    model = Entity
    form_class = EntityForm

    def get_success_url(self):
        if "popup" in self.kwargs:
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "app_name": "libtekin",
                    "model_name": "Entity",
                },
            )

        return reverse_lazy("libtekin:entity-detail", kwargs={"pk": self.object.pk})


class EntityDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_entity"
    model = Entity


class EntityDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "libtekin.delete_entity"
    model = Entity
    success_url = reverse_lazy("libtekin:entity-list")


class EntityList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_entity"
    model = Entity


class EntityClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_entity"
    model = Entity
    template_name = "libtekin/entity_closer.html"


def get_primary_id_field(request, mmodel_id):
    try:
        return Mmodel.objects.get(pk=mmodel_id).primary_id_field
    except ObjectDoesNotExist:
        return None


def count_primary_id(request, pk=0, primary_id=""):
    if int(pk) > 0:
        return HttpResponse(
            Item.objects.filter(primary_id=primary_id).exclude(pk=pk).count()
        )
    else:
        return HttpResponse(Item.objects.filter(primary_id=primary_id).count())


class ItemNoteCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_itemnote"
    model = ItemNote
    form_class = ItemNoteForm

    def form_valid(self, form):
        response = super().form_valid(form)

        update_history(form, "ItemNote", form.instance, self.request.user)

        self.object = form.save()

        return response

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy(
                "libtekin:itemnote-close", kwargs={"pk": self.object.pk}
            )
        else:
            return reverse_lazy(
                "libtekin:itemnote-detail", kwargs={"pk": self.object.pk}
            )


class ItemNoteUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_itemnote"
    model = ItemNote
    form_class = ItemNoteForm

    def form_valid(self, form):
        update_history(form, "ItemNote", form.instance, self.request.user)

        response = super().form_valid(form)

        self.object = form.save()

        return response

    def get_success_url(self):
        return reverse_lazy("libtekin:itemnote-detail", kwargs={"pk": self.object.pk})


class ItemNoteDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_itemnote"
    model = ItemNote

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["itemnote_labels"] = {
            field.name: field.verbose_name.title()
            for field in ItemNote._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        context_data["item_labels"] = {
            field.name: field.verbose_name.title()
            for field in Item._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class ItemNoteDelete(PermissionRequiredMixin, DeleteView):
    permission_required = "libtekin.delete_itemnote"
    model = ItemNote
    success_url = reverse_lazy("libtekin:itemnote-list")


class ItemNoteSoftDelete(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.delete_itemnote"
    model = ItemNote
    template_name = "libtekin/itemnote_confirm_delete.html"
    success_url = reverse_lazy("libtekin:itemnote-list")
    fields = ["is_deleted"]

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["itemnote_labels"] = {
            field.name: field.verbose_name.title()
            for field in ItemNote._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        context_data["item_labels"] = {
            field.name: field.verbose_name.title()
            for field in Item._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class ItemNoteList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_itemnote"
    model = ItemNote
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["count"] = self.object_list.count()

        return context_data


class ItemNoteCategoryCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_itemnotecategory"
    model = ItemNoteCategory
    form_class = ItemNoteCategoryForm

    def form_valid(self, form):
        response = super().form_valid(form)

        update_history(form, "ItemNoteCategory", form.instance, self.request.user)

        self.object = form.save()

        return response

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy(
                "libtekin:itemnotecategory-close", kwargs={"pk": self.object.pk}
            )
        else:
            return reverse_lazy(
                "libtekin:itemnotecategory-detail", kwargs={"pk": self.object.pk}
            )


class ItemNoteCategoryUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_itemnotecategory"
    model = ItemNoteCategory
    form_class = ItemNoteCategoryForm

    def form_valid(self, form):
        update_history(form, "ItemNoteCategory", form.instance, self.request.user)

        response = super().form_valid(form)

        self.object = form.save()

        return response

    def get_success_url(self):
        return reverse_lazy(
            "libtekin:itemnotecategory-detail", kwargs={"pk": self.object.pk}
        )


class ItemNoteCategoryDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_itemnotecategory"
    model = ItemNoteCategory

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["itemnotecategory_labels"] = {
            field.name: field.verbose_name.title()
            for field in ItemNoteCategory._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }
        context_data["item_labels"] = {
            field.name: field.verbose_name.title()
            for field in Item._meta.get_fields()
            if type(field).__name__[-3:] != "Rel"
        }

        return context_data


class ItemNoteCategoryDelete(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.delete_itemnotecategory"
    model = ItemNoteCategory
    success_url = reverse_lazy("libtekin:itemnotecategory-list")


class ItemNoteCategoryList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_itemnotecategory"
    model = ItemNoteCategory


class ItemNoteCategoryClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_itemnotecategory"
    model = ItemNoteCategory
    template_name = "libtekin/itemnotecategory_closer.html"


class MemberCreate(PermissionRequiredMixin, CreateView):
    permission_required = "spl_members.add_member"
    model = Member
    form_class = MemberForm
    template_name = "libtekin/member_create.html"

    def get_template_names(self):
        template_names = super().get_template_names()
        print("tp2451749", template_names)
        return template_names

    def get_success_url(self):

        if "popup" in self.request.get_full_path():
            return reverse(
                "touglates:popup_closer",
                kwargs={
                    "pk": self.object.pk,
                    "app_name": "spl_members",
                    "model_name": "Member",
                },
            )
        return reverse_lazy("spl_members:member-detail", kwargs={"pk": self.object.pk})


class MemberDetail(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_Member"
    model = Member
