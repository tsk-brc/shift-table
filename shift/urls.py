from django.urls import path
from . import views

urlpatterns = [
    path('', views.shift_table, name='shift_table'),
    path('save/', views.save_shift, name='save_shift'),
    path('delete/<int:shift_id>/', views.delete_shift, name='delete_shift'),
] 