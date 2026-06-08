from django.urls import path
from . import views

app_name = 'game1example'

urlpatterns = [

    path('home/', views.game1example, name='game1example'),
]