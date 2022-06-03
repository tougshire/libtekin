from django.views.generic.base import RedirectView
from django.urls import path, reverse_lazy
from . import views

app_name = 'libtekin'

urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('libtekin:item-list'))),
    path('item/', RedirectView.as_view(url=reverse_lazy('libtekin:item-list'))),
    path('item/create/', views.ItemCreate.as_view(), name='item-create'),
    path('item/<int:pk>/update/', views.ItemUpdate.as_view(), name='item-update'),
    path('item/<int:pk>/detail/', views.ItemDetail.as_view(), name='item-detail'),
    path('item/<int:pk>/delete/', views.ItemSoftDelete.as_view(), name='item-delete'),
    path('item/list/', views.ItemList.as_view(), name='item-list'),
    path('item/csv/', views.ItemCSV.as_view(), name='item-csv'),
    path('item/<int:pk>/close/', views.ItemClose.as_view(), name="item-close"),
    path('item/<int:pk>/copy/', views.ItemCopy.as_view(), name='item-copy'),
    path('item/<str:copied_from>/copied/', views.ItemList.as_view(), name='item-copied'),
    path('entity/', RedirectView.as_view(url=reverse_lazy('libtekin:entity-list'))),
    path('entity/create/', views.EntityCreate.as_view(), name='entity-create'),
    path('entity/<int:pk>/update/', views.EntityUpdate.as_view(), name='entity-update'),
    path('entity/<int:pk>/detail/', views.EntityDetail.as_view(), name='entity-detail'),
    path('entity/<int:pk>/delete/', views.EntityDelete.as_view(), name='entity-delete'),
    path('entity/list/', views.EntityList.as_view(), name='entity-list'),
    path('entity/<int:pk>/close/', views.EntityClose.as_view(), name="entity-close"),
    path('location/', RedirectView.as_view(url=reverse_lazy('libtekin:location-list'))),
    path('location/create/', views.LocationCreate.as_view(), name='location-create'),
    path('location/<int:pk>/update/', views.LocationUpdate.as_view(), name='location-update'),
    path('location/<int:pk>/detail/', views.LocationDetail.as_view(), name='location-detail'),
    path('location/<int:pk>/delete/', views.LocationDelete.as_view(), name='location-delete'),
    path('location/list/', views.LocationList.as_view(), name='location-list'),
    path('location/<int:pk>/close/', views.LocationClose.as_view(), name="location-close"),
    path('mmodel/', RedirectView.as_view(url=reverse_lazy('libtekin:mmodel-list'))),
    path('mmodel/create/', views.MmodelCreate.as_view(), name='mmodel-create'),
    path('mmodel/<int:pk>/update/', views.MmodelUpdate.as_view(), name='mmodel-update'),
    path('mmodel/<int:pk>/detail/', views.MmodelDetail.as_view(), name='mmodel-detail'),
    path('mmodel/<int:pk>/delete/', views.MmodelDelete.as_view(), name='mmodel-delete'),
    path('mmodel/list/', views.MmodelList.as_view(), name='mmodel-list'),
    path('mmodel/<int:pk>/close/', views.MmodelClose.as_view(), name="mmodel-close"),
    path('mmodelcategory/create/', views.MmodelCategoryCreate.as_view(), name='mmodelcategory-create'),
    path('mmodelcategory/<int:pk>/update/', views.MmodelCategoryUpdate.as_view(), name='mmodelcategory-update'),
    path('mmodelcategory/<int:pk>/detail/', views.MmodelCategoryDetail.as_view(), name='mmodelcategory-detail'),
    path('mmodelcategory/<int:pk>/delete/', views.MmodelCategoryDelete.as_view(), name='mmodelcategory-delete'),
    path('mmodelcategory/list/', views.MmodelCategoryList.as_view(), name='mmodelcategory-list'),
    path('mmodelcategory/<int:pk>/close/', views.MmodelCategoryClose.as_view(), name="mmodelcategory-close"),
    path('mmodel/<int:pk>/primary_id_field/', views.get_primary_id_field, name="get_primary_id_field"),
#    path('item/list/by/<fieldname>/<query>/', views.ItemList.as_view(), name='item-list-search'),

]
