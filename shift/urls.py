from django.urls import path
from . import views

urlpatterns = [
    path('', views.shift_table, name='shift_table'),
] 