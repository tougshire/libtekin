from django.contrib import admin

from .models import (Condition, Entity, EntityCategory, Item, ItemNote, ItemNoteCategory, Location, LocationCategory, Mmodel,
                     MmodelCategory, History, Status)

admin.site.register(Condition)
admin.site.register(EntityCategory)
admin.site.register(Entity)
admin.site.register(ItemNote)
admin.site.register(Location)
admin.site.register(LocationCategory)
admin.site.register(MmodelCategory)
admin.site.register(Mmodel)
admin.site.register(ItemNoteCategory)

class ItemAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return Item.all_objects
    ordering = ['is_deleted'] + Item._meta.ordering

admin.site.register(Item, ItemAdmin)

admin.site.register(History)

class StatusAdmin(admin.ModelAdmin):
    list_display=('name', 'is_active', 'is_default',)

admin.site.register(Status, StatusAdmin)
