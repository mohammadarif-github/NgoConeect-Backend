from django.urls import path

from .views import (
    AdminResetPasswordView, AdminUserDetailView, AdminUserListView,
    ChangePasswordView, CustomTokenObtainPairView, ForgotPasswordView,
    LogoutView, ProfileView, RegistrationView, ResetPasswordView,
    TokenRefreshView,
)

urlpatterns = [
    # Auth
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Profile & Password
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    # Admin User Management
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<int:user_id>/reset-password/', AdminResetPasswordView.as_view(), name='admin_reset_password'),
]