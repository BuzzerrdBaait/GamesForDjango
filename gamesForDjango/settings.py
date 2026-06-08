"""
SETTINGS for gamesForDjango project.

Django Docs:

For more information on this file, see
https://docs.djangoproject.com/en/6.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path
import os

# This is a helper to generate a random key incase the developer
# forgets to set their environment variable.
def generate_key(length=50):
    import random
    import string
    """Generate a random string of letters and digits."""
    characters = string.ascii_letters + string.digits
    generated_chars = []
    for _ in range(length):
        generated_chars.append(random.choice(characters))
    return ''.join(generated_chars)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

try:
    SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
except:
    print("\n\n WARNING: DJANGO_SECRET_KEY environment variable not found. Please create the environment variable named DJANGO_SECRET_KEY. \n\nGenerating a key for now \n\n")
    SECRET_KEY = generate_key()


DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'menu',
    'game1example',
    'profileManagement'

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gamesForDjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [

            # This is where you let django know to add more template directories, each app get's their own.
            BASE_DIR / 'menu' / 'templates',
            BASE_DIR / 'game1example' / 'templates',
            BASE_DIR / 'profileManagement' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_DIRS=[

    # This is where we let django know where to look for our static files in development.
    # Notice that in production you will be using a provider like AWS. This is only to serve
    # your files while you edit and test them before pushing them to production.

    BASE_DIR / 'menu' / 'static' / 'javascript',
    BASE_DIR / 'menu' / 'static' / 'stylingCSS',

    BASE_DIR / 'game1example' / 'static' / 'javascript',
    BASE_DIR / 'game1example' / 'static' / 'stylingCSS',

    BASE_DIR / 'profileManagement' / 'static' / 'javascript',
    BASE_DIR / 'profileManagement' / 'static' / 'stylingCSS',
]


MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


WSGI_APPLICATION = 'gamesForDjango.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
