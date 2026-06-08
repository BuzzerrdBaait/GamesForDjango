
from django.urls import path, include

from . import views

app_name='profileManagement'

urlpatterns=[

     path('userProfile/', views.userProfileHome, name='userProfileHome'),

     path('login/', views.loginUser, name='loginUser'),

     path('logout/', views.logoutUser, name='logoutUser'),

     path('register/', views.registration, name='register'),

     path('verify/<str:authentication_link>/', views.authenticate_user, name='authenticate_user'),

     # ── Friend system ──────────────────────────────────────────────────────
     path('friends/search/', views.search_users, name='search_users'),
     path('friends/request/send/', views.send_friend_request, name='send_friend_request'),
     path('friends/request/<int:request_id>/respond/', views.respond_friend_request, name='respond_friend_request'),
     path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),

     # ── Messaging ──────────────────────────────────────────────────────────
     path('messages/unread/', views.get_unread_count, name='get_unread_count'),
     path('messages/<int:user_id>/', views.get_conversation, name='get_conversation'),
     path('messages/send/', views.send_message, name='send_message'),

     # ── User Options ───────────────────────────────────────────────────────
     path('options/save/', views.save_options, name='save_options'),
]
