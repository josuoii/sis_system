import os
from django.core.asgi import get_asgi_application

# FIRST set the default settings module before importing anything that needs Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pdie_system.settings')

# THEN get the Django ASGI application loaded first
django_asgi_app = get_asgi_application()

# Only AFTER Django is loaded can we import other things safely
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import intervention.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            intervention.routing.websocket_urlpatterns
        )
    ),
})