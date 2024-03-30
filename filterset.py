import django_filters
from .models import Item, Mmodel
from django.db import models
from django import forms
from django_filters_stoex.filters import CrossFieldSearchFilter
from touglates.widgets import DropdownSelectMultiple


class ItemFilter(django_filters.FilterSet):

    combined_text_search = CrossFieldSearchFilter(
        label="Text Search",
        field_name="common_name,mmodel__model_name,network_name,serial_number,service_number,asset_number,assignee__full_name,assignee__friendly_name,barcode",
        lookup_expr="icontains",
    )
    primary_id = django_filters.CharFilter(
        label="Primary ID", field_name="primary_id", lookup_expr="icontains"
    )
    common_name = django_filters.CharFilter(
        label="Common Name", field_name="common_name", lookup_expr="icontains"
    )
    mmodel__in = django_filters.ModelMultipleChoiceFilter(
        widget=DropdownSelectMultiple,
        field_name="mmodel",
        label="Model",
        queryset=Mmodel.objects.all(),
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
    barcode = django_filters.CharFilter(
        label="barcode", field_name="barcode", lookup_expr="icontains"
    )
    network_name = django_filters.CharFilter(
        label="Network Name", field_name="network_name", lookup_expr="icontains"
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
