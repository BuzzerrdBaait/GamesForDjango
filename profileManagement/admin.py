
                    #BlazingSugarCookies's Admin.py
from django.contrib import admin
from .models import userProfile

@admin.register(userProfile)

class UserProfileInfoInfo(admin.ModelAdmin):
     list_display=('username','email','is_verified')

### REGISTER MODELS FOR ADMIN HERE ###
