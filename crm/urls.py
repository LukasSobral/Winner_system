from django.urls import path
from . import views

urlpatterns = [
    path('', views.lead_list, name='lead_list'),
    path('create/ajax/', views.lead_create_ajax, name='lead_create_ajax'),
    path('<int:lead_id>/', views.lead_detail, name='lead_detail'),
    path('<int:lead_id>/edit/ajax/', views.lead_edit_ajax, name='lead_edit_ajax'),
    path('<int:lead_id>/delete/ajax/', views.lead_delete_ajax, name='lead_delete_ajax'),
]
