from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify that the service is running.
    """
    return Response({"status": "ok"})