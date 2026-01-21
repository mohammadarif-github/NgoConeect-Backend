from django.urls import path

from . import views

urlpatterns = [
    path('initiate/', views.InitiateDonationView.as_view(), name='donation-initiate'),
    path('payment/success/', views.PaymentSuccessView.as_view(), name='payment-success'),
    path('payment/fail/', views.PaymentFailView.as_view(), name='payment-fail'),
    path('payment/cancel/', views.PaymentCancelView.as_view(), name='payment-cancel'),
    path('public/', views.PublicDonationListView.as_view(), name='donation-public-list'),
    path('admin/', views.AdminDonationListView.as_view(), name='donation-admin-list'),
    path('admin/export/', views.ExportDonationsView.as_view(), name='donation-export-csv'),
]
