from django.contrib.sessions.exceptions import SessionInterrupted
from django.shortcuts import redirect
from django.urls import reverse

class SessionInterruptedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except SessionInterrupted:
            return redirect(reverse('session_interrupted'))
        return response 