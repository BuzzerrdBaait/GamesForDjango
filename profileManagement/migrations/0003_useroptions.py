from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profileManagement', '0002_message_friendrequest'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserOptions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timezone', models.CharField(
                    choices=[
                        ('local', 'Local'),
                        ('America/New_York', 'Eastern (ET)'),
                        ('America/Chicago', 'Central (CT)'),
                        ('America/Denver', 'Mountain (MT)'),
                        ('America/Los_Angeles', 'Pacific (PT)'),
                        ('America/Anchorage', 'Alaska (AKT)'),
                        ('Pacific/Honolulu', 'Hawaii (HT)'),
                        ('UTC', 'UTC'),
                        ('Europe/London', 'London (GMT/BST)'),
                        ('Europe/Paris', 'Central Europe (CET)'),
                        ('Europe/Moscow', 'Moscow (MSK)'),
                        ('Asia/Dubai', 'Dubai (GST)'),
                        ('Asia/Kolkata', 'India (IST)'),
                        ('Asia/Shanghai', 'China (CST)'),
                        ('Asia/Tokyo', 'Japan (JST)'),
                        ('Australia/Sydney', 'Sydney (AEST)'),
                        ('Pacific/Auckland', 'Auckland (NZST)'),
                    ],
                    default='local',
                    max_length=50,
                )),
                ('color_theme', models.CharField(
                    choices=[
                        ('forest', 'Forest'),
                        ('midnight', 'Midnight'),
                        ('ember', 'Ember'),
                        ('ocean', 'Ocean'),
                        ('light', 'Light'),
                    ],
                    default='forest',
                    max_length=20,
                )),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='options',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
    ]
