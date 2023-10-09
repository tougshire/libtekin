import csv
import sys
import logging

from typing import Any, Dict
import urllib
from urllib.parse import urlencode

from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.http import QueryDict
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView

from tougshire_vistas.models import Vista
from tougshire_vistas.views import (
    delete_vista,
    get_latest_vista,
    get_vista_queryset,
    make_vista,
    make_vista_fields,
    retrieve_vista,
    vista_context_data,
)

from .forms import (
    EntityForm,
    ItemBorrowerFormset,
    ItemCopyForm,
    ItemForm,
    ItemNoteCategoryForm,
    ItemNoteForm,
    ItemItemNoteFormset,
    ItemAssigneeFormset,
    LocationForm,
    MmodelCategoryForm,
    MmodelForm,
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
        formsetvar = {}
        formsets_valid = True
        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                formsetvar[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )
            else:
                formsetvar[formsetkey] = formsetclass(instance=self.object)

            if not (formsetvar[formsetkey]).is_valid():
                print("tp23a6k55", formsetkey)
                print(
                    "tp23a6k56", formsetvar[formsetkey], formsetvar[formsetkey].errors
                )

                for err in formsetvar[formsetkey].errors:
                    print("tp23a6k57", err)
                    form.add_error(None, err)
                    for formsetform in formsetvar[formsetkey].forms:
                        print("tp23a6k58")
                        for err in formsetform.errors:
                            print("tp23a6k59", err)
                            form.add_error(None, err)
                formsets_valid = False

        if not formsets_valid:
            print("tp23a6l00")

            return self.form_invalid(form)

        return response

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy("libtekin:item-close", kwargs={"pk": self.object.pk})
        else:
            return reverse_lazy("libtekin:item-detail", kwargs={"pk": self.object.pk})


class ItemUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_item"
    model = Item
    form_class = ItemForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

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

        update_history(form, "Item", form.instance, self.request.user)

        self.object = form.save()

        formsetclasses = {
            "itemnotes": ItemItemNoteFormset,
            "itemborrowers": ItemBorrowerFormset,
            "itemAssignees": ItemAssigneeFormset,
        }
        formsetvar = {}
        formsets_valid = True
        for formsetkey, formsetclass in formsetclasses.items():
            if self.request.POST:
                formsetvar[formsetkey] = formsetclass(
                    self.request.POST, instance=self.object
                )
            else:
                formsetvar[formsetkey] = formsetclass(instance=self.object)

            if (formsetvar[formsetkey]).is_valid():
                formsetvar[formsetkey].save()
            else:
                formsets_valid = False

        if formsets_valid:
            return response
        else:
            return self.form_invalid(form)

    def get_success_url(self):
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


class ItemCopy(DetailView, FormView):
    permission_required = "libtekin.add_item"
    template_name = "libtekin/item_confirm_copy.html"
    form_class = ItemCopyForm
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

    def form_valid(self, form):
        item = Item.objects.get(pk=self.kwargs.get("pk"))
        qty = form.cleaned_data["qty"]
        primary_id = item.primary_id
        for n in range(0, qty):
            item.pk = None
            item.primary_id = "[copy of] " + primary_id
            setattr(item, item.primary_id_field, "[copy of] " + primary_id)
            item.save()  # item is now a new item, the original item is untouched

        self.request.session["query"] = (
            "filter__fieldname__0=primary_id&filter__op__0=contains&filter__value__0=[copy of] "
            + primary_id
        )

        return redirect("libtekin:item-list")


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


class ItemList(PermissionRequiredMixin, ListView):
    permission_required = "libtekin.view_item"
    model = Item
    paginate_by = 30

    def setup(self, request, *args, **kwargs):
        self.vista_settings = {
            "max_search_keys": 5,
            "fields": [],
        }

        self.vista_settings["fields"] = make_vista_fields(
            Item,
            field_names=[
                "primary_id",
                "common_name",
                "mmodel",
                "mmodel__category",
                "mmodel__model_name",
                "network_name",
                "serial_number",
                "phone_number",
                "essid",
                "asset_number",
                "barcode",
                "phone_number",
                "role",
                "connected_to",
                "essid",
                "owner",
                "assignee",
                "itemassignee__entity",
                "borrower",
                "itemborrower__entity",
                "home",
                "location",
                "status",
                "connected_to__mmodel",
                "connection__mmodel",
                "latest_inventory",
                "installation_date",
                "status__is_active",
            ],
        )
        self.vista_settings["fields"]["assignee"]["label"] = "Current Assignee"
        self.vista_settings["fields"]["itemassignee__entity"]["label"] = "Assignees"

        self.vista_settings["fields"]["latest_update_date"] = {
            "type": "DateField",
            "label": "Latest Major Update Date",
            "available_for": ["order_by"],
        }
        self.vista_settings["fields"]["mmodel__model_name"]["available_for"] = [
            "quicksearch"
        ]

        self.vista_defaults = QueryDict(
            urlencode(
                [
                    ("filter__fieldname__0", ["status__is_active"]),
                    ("filter__op__0", ["exact"]),
                    ("filter__value__0", [True]),
                    ("order_by", ["primary_id", "common_name"]),
                    ("paginate_by", self.paginate_by),
                ],
                doseq=True,
            ),
            mutable=True,
        )

        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()

        self.vistaobj = {"querydict": QueryDict(), "queryset": queryset}

        return get_vista_queryset(self)

    def get_paginate_by(self, queryset):
        if (
            "paginate_by" in self.vistaobj["querydict"]
            and self.vistaobj["querydict"]["paginate_by"]
        ):
            return self.vistaobj["querydict"]["paginate_by"]

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        vista_data = vista_context_data(self.vista_settings, self.vistaobj["querydict"])
        vista_data["labels"]["Item"] = "item"

        context_data = {**context_data, **vista_data}
        context_data["vista_default"] = dict(self.vista_defaults)

        context_data["vistas"] = Vista.objects.filter(
            user=self.request.user, model_name="libtekin.item"
        ).all()  # for choosing saved vistas

        if self.request.POST.get("vista_name"):
            context_data["vista_name"] = self.request.POST.get("vista_name")

        context_data["count"] = self.object_list.count()

        return context_data


class ItemCSV(ItemList):
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="items.csv"'},
        )

        writer = csv.writer(response)
        vista_data = vista_context_data(self.vista_settings, self.vistaobj["querydict"])

        row = []

        if (
            not "show_columns" in vista_data
            or "common_name" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["common_name"])
        if not "show_columns" in vista_data or "mmodel" in vista_data["show_columns"]:
            row.append(context["labels"]["mmodel"])
        if (
            not "show_columns" in vista_data
            or "primary_id" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["primary_id"])
        if (
            not "show_columns" in vista_data
            or "serial_number" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["serial_number"])
        if (
            not "show_columns" in vista_data
            or "phone_number" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["phone_number"])
        if (
            not "show_columns" in vista_data
            or "asset_number" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["asset_number"])
        if not "show_columns" in vista_data or "barcode" in vista_data["show_columns"]:
            row.append(context["labels"]["barcode"])
        if (
            not "show_columns" in vista_data
            or "network_name" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["network_name"])
        if (
            not "show_columns" in vista_data
            or "phone_number" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["phone_number"])
        if not "show_columns" in vista_data or "essid" in vista_data["show_columns"]:
            row.append(context["labels"]["essid"])
        if not "show_columns" in vista_data or "role" in vista_data["show_columns"]:
            row.append(context["labels"]["role"])
        if (
            not "show_columns" in vista_data
            or "connected_to" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["connected_to"])
        if not "show_columns" in vista_data or "status" in vista_data["show_columns"]:
            row.append(context["labels"]["status"])
        if not "show_columns" in vista_data or "home" in vista_data["show_columns"]:
            row.append(context["labels"]["home"])
        if not "show_columns" in vista_data or "location" in vista_data["show_columns"]:
            row.append(context["labels"]["location"])
        if not "show_columns" in vista_data or "assignee" in vista_data["show_columns"]:
            row.append(context["labels"]["assignee"])
        if not "show_columns" in vista_data or "borrower" in vista_data["show_columns"]:
            row.append(context["labels"]["borrower"])
        if not "show_columns" in vista_data or "owner" in vista_data["show_columns"]:
            row.append(context["labels"]["owner"])
        if (
            not "show_columns" in vista_data
            or "latest_inventory" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["latest_inventory"])
        if (
            not "show_columns" in vista_data
            or "installation_date" in vista_data["show_columns"]
        ):
            row.append(context["labels"]["installation_date"])

        writer.writerow(row)

        for item in self.object_list:
            row = []
            if (
                not "show_columns" in vista_data
                or "common_name" in vista_data["show_columns"]
            ):
                row.append(item.common_name)
            if (
                not "show_columns" in vista_data
                or "mmodel" in vista_data["show_columns"]
            ):
                row.append(item.mmodel)
            if (
                not "show_columns" in vista_data
                or "primary_id" in vista_data["show_columns"]
            ):
                row.append(item.primary_id)
            if (
                not "show_columns" in vista_data
                or "serial_number" in vista_data["show_columns"]
            ):
                row.append(item.serial_number)
            if (
                not "show_columns" in vista_data
                or "phone_number" in vista_data["show_columns"]
            ):
                row.append(item.phone_number)
            if (
                not "show_columns" in vista_data
                or "asset_number" in vista_data["show_columns"]
            ):
                row.append(item.asset_number)
            if (
                not "show_columns" in vista_data
                or "barcode" in vista_data["show_columns"]
            ):
                row.append(item.barcode)
            if (
                not "show_columns" in vista_data
                or "network_name" in vista_data["show_columns"]
            ):
                row.append(item.network_name)
            if (
                not "show_columns" in vista_data
                or "phone_number" in vista_data["show_columns"]
            ):
                row.append(item.phone_number)
            if (
                not "show_columns" in vista_data
                or "essid" in vista_data["show_columns"]
            ):
                row.append(item.essid)
            if not "show_columns" in vista_data or "role" in vista_data["show_columns"]:
                row.append(item.role)
            if (
                not "show_columns" in vista_data
                or "connected_to" in vista_data["show_columns"]
            ):
                row.append(item.connected_to)
            if (
                not "show_columns" in vista_data
                or "status" in vista_data["show_columns"]
            ):
                row.append(item.status)
            if not "show_columns" in vista_data or "home" in vista_data["show_columns"]:
                row.append(item.home)
            if (
                not "show_columns" in vista_data
                or "location" in vista_data["show_columns"]
            ):
                row.append(item.location)
            if (
                not "show_columns" in vista_data
                or "assignee" in vista_data["show_columns"]
            ):
                row.append(item.assignee)
            if (
                not "show_columns" in vista_data
                or "borrower" in vista_data["show_columns"]
            ):
                row.append(item.borrower)
            if (
                not "show_columns" in vista_data
                or "owner" in vista_data["show_columns"]
            ):
                row.append(item.owner)
            if (
                not "show_columns" in vista_data
                or "latest_inventory" in vista_data["show_columns"]
            ):
                row.append(item.latest_inventory)
            if (
                not "show_columns" in vista_data
                or "installation_date" in vista_data["show_columns"]
            ):
                row.append(item.installation_date)

            writer.writerow(row)

        return response


class ItemClose(PermissionRequiredMixin, DetailView):
    permission_required = "libtekin.view_item"
    model = Item
    template_name = "libtekin/item_closer.html"


class MmodelCreate(PermissionRequiredMixin, CreateView):
    permission_required = "libtekin.add_mmodel"
    model = Mmodel
    form_class = MmodelForm

    def get_success_url(self):
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy("libtekin:mmodel-close", kwargs={"pk": self.object.pk})
        else:
            return reverse_lazy("libtekin:mmodel-detail", kwargs={"pk": self.object.pk})

        return response


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
        if "opener" in self.request.POST and self.request.POST["opener"] > "":
            return reverse_lazy("libtekin:entity-close", kwargs={"pk": self.object.pk})
        else:
            return reverse_lazy("libtekin:entity-detail", kwargs={"pk": self.object.pk})


class EntityUpdate(PermissionRequiredMixin, UpdateView):
    permission_required = "libtekin.change_entity"
    model = Entity
    form_class = EntityForm

    def get_success_url(self):
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
        print("tp 2271431", primary_id)
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

    def setup(self, request, *args, **kwargs):
        self.vista_settings = {
            "max_search_keys": 5,
            "fields": [],
        }

        self.vista_settings["fields"] = make_vista_fields(
            ItemNote,
            field_names=[
                "item",
                "level",
                "flagged",
                "when",
                "itemnotecategory",
                "maintext",
                "details",
                "item__status__is_active",
                "item__primary_id",
                "level",
            ],
        )

        self.vista_defaults = QueryDict(
            urlencode(
                [
                    ("filter__fieldname__0", ["flagged"]),
                    ("filter__op__0", ["gt"]),
                    ("filter__value__0", [0]),
                    ("order_by", ["when", "item"]),
                    ("paginate_by", self.paginate_by),
                    ("filter__fieldname__1", ["item__status__is_active"]),
                    ("filter__op__1", ["exact"]),
                    ("filter__value__1", [True]),
                ],
                doseq=True,
            ),
            mutable=True,
        )

        return super().setup(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset()

        self.vistaobj = {"querydict": QueryDict(), "queryset": queryset}

        return get_vista_queryset(self)

    def get_paginate_by(self, queryset):
        if (
            "paginate_by" in self.vistaobj["querydict"]
            and self.vistaobj["querydict"]["paginate_by"]
        ):
            return self.vistaobj["querydict"]["paginate_by"]

        return super().get_paginate_by(self)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        vista_data = vista_context_data(self.vista_settings, self.vistaobj["querydict"])

        context_data = {**context_data, **vista_data}
        context_data["vista_default"] = dict(self.vista_defaults)

        context_data["vistas"] = Vista.objects.filter(
            user=self.request.user, model_name="libtekin.itemnote"
        ).all()  # for choosing saved vistas

        if self.request.POST.get("vista_name"):
            context_data["vista_name"] = self.request.POST.get("vista_name")

        context_data["count"] = self.object_list.count()

        return context_data


################


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
