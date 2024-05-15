from django.http import QueryDict
import django_filters

from django_filters_stoex.filterset import StoexFilterSet
from spl_members.models import Member
from .models import Item, Mmodel, MmodelCategory, Role, Status
from django.db import models
from django import forms
from django_filters_stoex.filters import CrossFieldSearchFilter
from touglates.widgets import DropdownSelectMultiple


class ItemFilter(StoexFilterSet):

    combined_text_search = CrossFieldSearchFilter(
        label="Text Search",
        field_name="common_name,mmodel__model_name,network_name,serial_number,service_number,asset_number,assignee__name_full,assignee__name_prefered,barcode",
        lookup_expr="icontains",
    )
    primary_id = django_filters.CharFilter(
        label="Primary ID",
        field_name="primary_id",
        lookup_expr="icontains",
    )
    common_name = django_filters.CharFilter(
        label="Common Name",
        field_name="common_name",
        lookup_expr="icontains",
    )
    role__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="role",
        label="Role",
        queryset=Role.objects.all(),
    )
    assignee__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="assignee",
        label="Current Assignee",
        queryset=Member.objects.all(),
    )
    historical_assignements__assignee__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="historical_assignements__assignee",
        label="Historical Assignees",
        queryset=Member.objects.all(),
    )
    borrower__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="borrower",
        label="Current Borrower",
        queryset=Member.objects.all(),
    )
    historical_borrow__borrower__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="historical_borrow__borrower",
        label="Historical Borrowers",
        queryset=Member.objects.all(),
    )
    mmodel__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="mmodel",
        label="Model",
        queryset=Mmodel.objects.all(),
    )
    mmodel__category__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="mmodel__category",
        label="Model Category",
        queryset=MmodelCategory.objects.all(),
    )
    serial_number = django_filters.CharFilter(
        label="Serial Number", field_name="serial_number", lookup_expr="icontains"
    )
    service_number = django_filters.CharFilter(
        label="Service Number", field_name="service_number", lookup_expr="icontains"
    )
    asset_number = django_filters.CharFilter(
        label="Asset Number", field_name="asset_number", lookup_expr="icontains"
    )
    barcode_icontains = django_filters.CharFilter(
        label="Barcode", field_name="barcode", lookup_expr="icontains"
    )
    network_name = django_filters.CharFilter(
        label="Network Name",
        field_name="network_name",
        lookup_expr=["icontains", "iexact"],
    )
    status__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="status",
        label="Status",
        queryset=Status.objects.all(),
    )
    status__is_active = django_filters.CharFilter(
        field_name="status__is_active", label="Active", initial="True"
    )

    # "phone_number",
    # "mobile_id",
    # "sim_iccid",
    # "connected_to",
    # "status",
    # "owner",
    # "home",
    # "latest_inventory",
    # "installation_date",
    # "location",
    # "role",

    orderbyfields = django_filters.OrderingFilter(
        fields=(
            "common_name",
            "mmodel",
            "primary_id_field",
            "serial_number",
            "service_number",
            "asset_number",
            "barcode",
            "phone_number",
            "mobile_id",
            "sim_iccid",
            "connected_to",
            "status",
            "network_name",
            "owner",
            "home",
            "latest_inventory",
            "installation_date",
            "location",
            "role",
        ),
    )

    class Meta:
        model = Item
        fields = [
            # "common_name",
            # "primary_id_field",
            # "serial_number",
            # "service_number",
            # "asset_number",
            # "barcode",
            # "phone_number",
            # "mobile_id",
            # "sim_iccid",
            # "connected_to",
            # "status",
            # "network_name",
            # "owner",
            # "home",
            # "latest_inventory",
            # "installation_date",
            # "location",
            # "role",
        ]
