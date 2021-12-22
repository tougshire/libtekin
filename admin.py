from django.contrib import admin

from .models import (Condition, Entity, EntityCategory, Item, ItemNote, Location, LocationCategory, Mmodel,
                     MmodelCategory, History)

admin.site.register(Condition)
admin.site.register(EntityCategory)
admin.site.register(Entity)
admin.site.register(ItemNote)
admin.site.register(Location)
admin.site.register(LocationCategory)
admin.site.register(MmodelCategory)
admin.site.register(Mmodel)

class ItemAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return Item.all_objects
    ordering = ['is_deleted'] + Item._meta.ordering

admin.site.register(Item, ItemAdmin)

admin.site.register(History)

