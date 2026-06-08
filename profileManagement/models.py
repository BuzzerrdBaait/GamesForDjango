
from django.db import models
#USER_PROFILE IMPORTS
from django.contrib.auth.models import AbstractUser
import secrets

class userProfile(AbstractUser):
    
    #ALTERING THE DJANGO BASE USER MODEL.  
    email=models.CharField(max_length=40, blank=True, null=True, unique=True)
    profile_picture=models.ImageField(upload_to='ilovecookbooks_profile_images',default="none")
    authentication_key= models.CharField(max_length=50, unique=True)
    is_verified = models.CharField(max_length=1, default='N')
    authentication_link= models.CharField(max_length=50, blank=True, null=True)
    
    def generate_unique_link(self):
        """Generate a URL-safe random token for the authentication link."""
        return secrets.token_urlsafe(30)


    def save(self, *args, **kwargs):
        
        # MAKES THE AUTHENTICATION KEY UPON USER CREATION .
        # CALLS generate_unique_link
        # also any other things we want to add upon user creation.

        if not self.authentication_key:
            self.authentication_key = secrets.token_urlsafe(30)
     
        if not self.authentication_link:
            self.authentication_link = self.generate_unique_link()

        super().save(*args,**kwargs)



class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    ]
    sender   = models.ForeignKey(userProfile, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(userProfile, on_delete=models.CASCADE, related_name='received_requests')
    status   = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} [{self.status}]"


class Message(models.Model):
    sender    = models.ForeignKey(userProfile, on_delete=models.CASCADE, related_name='sent_messages')
    receiver  = models.ForeignKey(userProfile, on_delete=models.CASCADE, related_name='received_messages')
    content   = models.TextField(max_length=2000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read   = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username}: {self.content[:40]}"


class UserOptions(models.Model):
    THEME_CHOICES = [
        ('forest',   'Forest'),
        ('midnight', 'Midnight'),
        ('ember',    'Ember'),
        ('ocean',    'Ocean'),
        ('light',    'Light'),
        ('rose',     'Rose Petal'),
        ('blush',    'Blush'),
        ('pearl',    'Pearl'),
        ('hxxr',     'Green HXXR'),
        ('win98',    'Windows 98'),
        ('doom',     'DOOM'),
        ('halo3',    'Halo 3'),
    ]
    TIMEZONE_CHOICES = [
        ('local',                'Local'),
        ('America/New_York',     'Eastern (ET)'),
        ('America/Chicago',      'Central (CT)'),
        ('America/Denver',       'Mountain (MT)'),
        ('America/Los_Angeles',  'Pacific (PT)'),
        ('America/Anchorage',    'Alaska (AKT)'),
        ('Pacific/Honolulu',     'Hawaii (HT)'),
        ('UTC',                  'UTC'),
        ('Europe/London',        'London (GMT/BST)'),
        ('Europe/Paris',         'Central Europe (CET)'),
        ('Europe/Moscow',        'Moscow (MSK)'),
        ('Asia/Dubai',           'Dubai (GST)'),
        ('Asia/Kolkata',         'India (IST)'),
        ('Asia/Shanghai',        'China (CST)'),
        ('Asia/Tokyo',           'Japan (JST)'),
        ('Australia/Sydney',     'Sydney (AEST)'),
        ('Pacific/Auckland',     'Auckland (NZST)'),
    ]

    TIME_FORMAT_CHOICES = [
        ('24h', '24-hour'),
        ('12h', '12-hour'),
    ]

    LANGUAGE_CHOICES = [
        ('en',      'English'),
        ('es',      'Español (Spanish)'),
        ('zh-hans', '中文 (Chinese Simplified)'),
        ('fr',      'Français (French)'),
        ('de',      'Deutsch (German)'),
        ('ja',      '日本語 (Japanese)'),
        ('pt',      'Português (Portuguese)'),
        ('ar',      'العربية (Arabic)'),
    ]

    user        = models.OneToOneField(userProfile, on_delete=models.CASCADE, related_name='options')
    timezone    = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='local')
    color_theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='forest')
    time_format = models.CharField(max_length=3, choices=TIME_FORMAT_CHOICES, default='24h')
    language    = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')

    def __str__(self):
        return f"{self.user.username} — tz:{self.timezone} theme:{self.color_theme} fmt:{self.time_format} lang:{self.language}"

    

