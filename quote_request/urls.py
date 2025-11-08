# In quote_request/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.quote_detail, name='quote_detail'),
    path('add/', views.add_to_quote, name='quote_add'),
    path('remove/', views.remove_from_quote, name='quote_remove'),
    path('update/', views.update_quote, name='quote_update'),
]