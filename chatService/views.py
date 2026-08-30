from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .services import query_chatbot

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

    res = query_chatbot(question)

    # query_chatbot returns 1 (int) on failure, a results dict on success
    if not isinstance(res, dict):
        return Response(
            {"error": "Could not query the knowledge index."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    docs = res["documents"][0]
    dists = res["distances"][0]
    metas = res["metadatas"][0]

    lines = []
    for i in range(len(docs)):
        m = metas[i]
        lines.append(
            f"--- result {i}  (distance {dists[i]:.4f})  "
            f"{m.get('source', '?')} page {m.get('page', '?')}  "
            f"chunk {m.get('chunk_index', '?')} ---"
        )
        lines.append(docs[i])

    answer_text = "\n".join(lines)

    return Response({"answer": [{"type": "text", "text": answer_text}]})      