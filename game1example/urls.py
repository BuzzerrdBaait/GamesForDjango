from django.urls import path
from . import views

urlpatterns = [

    path('game1example/', views.game1example, name='game1example'),
]