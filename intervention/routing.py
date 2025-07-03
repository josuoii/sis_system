from django.urls import re_path
from . import consumers
from .consumers import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
] 