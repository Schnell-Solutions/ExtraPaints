from django.urls import path

from . import views

urlpatterns = [
    path('', views.guide_list, name='guide_list'),
    path('<slug:slug>/', views.guide_detail, name='guide_detail'),
]
