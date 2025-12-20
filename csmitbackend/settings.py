import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

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
    'corsheaders',  # Ensure this is here
    'users', 'resume', 'practice', 'jobs', 'exams', 'doubts',
    'courses', 'batches', 'drf_yasg', 'announcements', 'inquiries',
    'success_stories', 'blogs', 'notes', 'careers',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Sabse upar hona chahiye
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

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'examDb',
        'HOST': 'localhost',
        'USER': '',  
        'PASSWORD': '', 
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',
            'trusted_connection': 'yes',
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

# ================= CORS & CSRF SETTINGS FOR NGROK =================
CORS_ALLOW_ALL_ORIGINS = True  # Development ke liye allow all safe hai
CORS_ALLOW_CREDENTIALS = True

# CSRF ke liye ngrok ka URL trust karna zaroori hai warna Login nahi hoga
CSRF_TRUSTED_ORIGINS = [
    "https://unwhistled-stefan-supernotable.ngrok-free.dev",
    "http://localhost:4200",
    "http://127.0.0.1:4200"
]
# =================================================================

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "shivkumarmatkawala@gmail.com"
EMAIL_HOST_PASSWORD = "ifqw brmt ihxm izqg" 
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# AWS Settings
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")

# MSSQL Version Fixes
import mssql.base
mssql.base.DatabaseWrapper._sql_server_versions['v17'] = 2022
if 'v16' in mssql.base.DatabaseWrapper.data_types_suffix:
    mssql.base.DatabaseWrapper.data_types_suffix['v17'] = mssql.base.DatabaseWrapper.data_types_suffix['v16']
else:
    mssql.base.DatabaseWrapper.data_types_suffix['v17'] = mssql.base.DatabaseWrapper.data_types_suffix.get('v15', '')

def fake_version(self):
    return 2022

mssql.base.DatabaseWrapper.sql_server_version = property(fake_version)