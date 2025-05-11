from django.urls import path
from .views import AppNotificationsView

app_name = 'notifications'

urlpatterns = [
    path('<str:app_id>/', AppNotificationsView.as_view(), name='app_notifications'),
]
