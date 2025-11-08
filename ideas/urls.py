from django.urls import path
from . import views

urlpatterns = [
    path('', views.idea_list, name='idea_list'),
    path('save-toggle/', views.save_idea_toggle, name='save_idea_toggle'),
    path('<slug:slug>/', views.idea_detail, name='idea_detail'),
]
