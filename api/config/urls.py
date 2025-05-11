from django.urls import path
from .views import ConfigurationDetailView

app_name = 'config'

urlpatterns = [
    path('configuration/', ConfigurationDetailView.as_view(), name='get_configuration'),
]
