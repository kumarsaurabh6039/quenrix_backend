from datetime import timedelta
import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env()
# Reading .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9qc9&1=t1oloyr_d73n+xqk1ngtzv(th*!6isth)kj_9x&8!#f'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Sabhi hosts allow kar rahe hain taaki ngrok se connection na tute
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'users', 'resume', 'practice', 'jobs', 'exams', 'doubts',
    'courses', 'batches', 'drf_yasg', 'announcements', 'inquiries',
    'success_stories', 'blogs', 'notes', 'careers', 'job_applications',
    'executor', 'zoom',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'csmitbackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'csmitbackend.wsgi.application'

# Database Configuration (MS SQL Server)
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='1433'),
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;',
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static and Media files
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "https://unwhistled-stefan-supernotable.ngrok-free.dev",
    "http://localhost:4200",
    "http://127.0.0.1:4200"
]

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "quenrix46@gmail.com"
EMAIL_HOST_PASSWORD = "ujvhooagipoepnsf"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# AWS Settings (Reads from .env)
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")

# AI Settings (Reads from .env)
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")

# Zoom Settings
ZOOM_CLIENT_ID = env("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = env("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_ID = env("ZOOM_ACCOUNT_ID")

# SQL Server Compatibility Fixes
import mssql.base
mssql.base.DatabaseWrapper._sql_server_versions['v17'] = 2022
if 'v16' in mssql.base.DatabaseWrapper.data_types_suffix:
    mssql.base.DatabaseWrapper.data_types_suffix['v17'] = mssql.base.DatabaseWrapper.data_types_suffix['v16']
else:
    mssql.base.DatabaseWrapper.data_types_suffix['v17'] = mssql.base.DatabaseWrapper.data_types_suffix.get('v15', '')

def fake_version(self):
    return 2022

mssql.base.DatabaseWrapper.sql_server_version = property(fake_version)

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'users.authentication.CustomJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=3),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_CLAIM': 'user_id',
}