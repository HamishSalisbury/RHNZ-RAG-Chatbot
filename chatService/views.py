from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify that the service is running.
    """
    return Response({"status": "ok"})

@api_view(['POST'])
def ask_chatbot(request):
    question = request.data.get('question') 
    if not question:
        return Response(
            {"error": "'question' is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
    return Response({"answer": [{"type":"text", "text": "Generic Hardcoded response"}]})
        