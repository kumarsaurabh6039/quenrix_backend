import requests
import base64
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
import environ
import os
from csmitbackend.settings import BASE_DIR

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

ZOOM_CLIENT_ID = env("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = env("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_ID = env("ZOOM_ACCOUNT_ID")


def get_zoom_access_token():
    token = cache.get("zoom_access_token")
    if token:
        print(token)
        return token
    

    url = "https://zoom.us/oauth/token"
    auth = base64.b64encode(
        f"{settings.ZOOM_CLIENT_ID}:{settings.ZOOM_CLIENT_SECRET}".encode()
    ).decode()

    headers = {"Authorization": f"Basic {auth}"}
    params = {
        "grant_type": "account_credentials",
        "account_id": settings.ZOOM_ACCOUNT_ID
    }

    res = requests.post(url, headers=headers, params=params)
    token = res.json()["access_token"]

    cache.set("zoom_access_token", token, timeout=3500)
    return token


def create_meeting(topic, start_time):
    token = get_zoom_access_token()

    url = "https://api.zoom.us/v2/users/me/meetings"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "topic": topic,
        "type": 2,
        "start_time": start_time,
        "duration": 60,
    }

    res = requests.post(url, json=payload, headers=headers)
    return res.json()


def get_recordings(user_id="me"):
    token = get_zoom_access_token()

    url = f"https://api.zoom.us/v2/users/{user_id}/recordings"
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get(url, headers=headers)
    return res.json()
