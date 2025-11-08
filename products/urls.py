from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('save-toggle/', views.save_product_toggle, name='save_product_toggle'),  # move this above
    path('<slug:slug>/', views.product_detail, name='product_detail'),
]

