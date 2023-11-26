"""
Django settings for mysite project.

Generated by 'django-admin startproject' using Django 2.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import sys
import mimetypes
from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f'[MYSITE.SETTINGS] settings path: {os.path.abspath(__file__)}')

# # SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'frh*4wr$jh5j(ny99*i=-gur7d)(=-#ldipq@m2gbpmsw1ast$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("text/javascript", ".js", True)

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mdict.apps.MdictConfig',
    'mynav.apps.MynavConfig',
    'ckeditor',
    'ckeditor_uploader',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.gzip.GZipMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # 设置网站根目录下的templates文件夹为模板的路径。
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

REST_FRAMEWORK = {

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',

    ),

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),

}

WSGI_APPLICATION = 'mysite.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
}

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

CKEDITOR_UPLOAD_PATH = "uploads/"  # ckeditor上传图片的存放位置是media/uploads/
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'width': '100%',
        'mathJaxLib': '/static/mdict/mathjax/2.7.9/MathJax.js?config=TeX-AMS_HTML',
        'extraPlugins': ','.join([
            'mathjax',
            'mlink',
            'mwrap',
            'mruby',
            'mbox',
        ]),
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,  # 关闭筛选，否则插入的ruby标签会被丢弃。
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
# 新版django会报警告Auto-created primary key used when not defining a primary key type

LANGUAGES = (
    ('en', _('English')),
    ('zh-Hans', _('Chinese Simplified')),
)

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000
# 超过设定值会报错：The number of GET/POST parameters exceeded settings.DATA_UPLOAD_MAX_NUMBER_FIELDS.

SECURE_CONTENT_TYPE_NOSNIFF = False
# django.middleware.security.SecurityMiddleware
# django3.0 SECURE_CONTENT_TYPE_NOSNIFF默认为True

X_FRAME_OPTIONS = 'SAMEORIGIN'
# django.middleware.clickjacking.XFrameOptionsMiddleware
# django3.0 X_FRAME_OPTIONS默认为DENY


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'collect_static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOGIN_URL = '/admin/login/'
