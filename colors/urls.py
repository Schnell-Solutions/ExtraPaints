from django.urls import path
from . import views

urlpatterns = [
    path("", views.color_list, name="color_list"),
    path("save-toggle/", views.save_color_toggle, name="save_color_toggle"),
    path("ajax-products/<int:color_id>/", views.ajax_get_color_products, name="ajax_get_color_products"),
    path("<slug:slug>/", views.color_detail, name="color_detail"),
]
