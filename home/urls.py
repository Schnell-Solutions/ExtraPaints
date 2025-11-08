from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('my-collection/', views.my_collection, name='my_collection'),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path('ajax/search/', views.live_search, name='live_search'),
path('ajax/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]
