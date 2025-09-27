from django.urls import path
from . import views

urlpatterns = [
    path('select-center/', views.select_center, name='select_center'),
    path('', views.list_records, name='record_list'),
    path('new/', views.create_record, name='record_create'),
    path('edit/<int:pk>/', views.edit_record, name='record_edit'),
    path('ajax/files/',     views.get_files,      name='get_files'),
    path('ajax/payment-types/', views.get_payment_types, name='get_payment_types'),
]