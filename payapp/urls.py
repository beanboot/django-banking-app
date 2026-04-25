from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('send/', views.send_payment, name='send_payment'),
    path('history/', views.transaction_history, name='transaction_history'),
    path('request/', views.request_payment, name='request_payment'),
    path('request/<int:pk>/', views.handle_payment_request, name='handle_payment_request'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/register/', views.register_admin, name='register_admin'),
]