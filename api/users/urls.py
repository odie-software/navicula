from django.urls import path
from .views import UserAppSettingsView

app_name = 'users'

urlpatterns = [
    path('settings/<str:app_id>/', UserAppSettingsView.as_view(), name='user_app_settings'),
]
