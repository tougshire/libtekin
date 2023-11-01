from django.contrib import admin

from .models import (
    Entity,
    EntityCategory,
    Item,
    ItemAssignee,
    ItemBorrower,
    ItemNote,
    ItemNoteCategory,
    ItemNoteLevel,
    Location,
    LocationCategory,
    Mmodel,
    MmodelCategory,
    History,
    Status,
)

admin.site.register(EntityCategory)
admin.site.register(Entity)
admin.site.register(Location)
admin.site.register(LocationCategory)
admin.site.register(MmodelCategory)
admin.site.register(Mmodel)
admin.site.register(ItemAssignee)
admin.site.register(ItemBorrower)
admin.site.register(ItemNoteCategory)


class ItemAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return Item.all_objects

    ordering = ["is_deleted"] + Item._meta.ordering


admin.site.register(Item, ItemAdmin)

admin.site.register(History)


class StatusAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "is_default",
    )


admin.site.register(Status, StatusAdmin)


class ItemNoteAdmin(admin.ModelAdmin):
    list_display = ["__str__", "level", "itemnotecategory"]
    list_filter = [
        "level",
    ]


admin.site.register(ItemNote, ItemNoteAdmin)

admin.site.register(ItemNoteLevel)
