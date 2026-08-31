from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, throttle_classes
from rest_framework import status
from .services import query_chatbot
from google.genai import errors
from .services import query_chatbot, generate_answer
from .throttles import BurstRateThrottle, SustainedRateThrottle

@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify that the service is running.
    """
    return Response({"status": "ok"})

@api_view(['POST'])
@throttle_classes([BurstRateThrottle, SustainedRateThrottle])
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
    metas = res["metadatas"][0]

    # nothing cleared the similarity threshold -> don't call the LLM
    if not docs:
        return Response({"answer": [{"type": "text",
            "text": "I couldn't find anything relevant in the rules."}]})

    # build the rules block: each chunk with its rule_id so the model can cite it
    rules_block = "\n\n".join(
        f"[{metas[i].get('rule_id', '?')}] {docs[i]}"
        for i in range(len(docs))
    )
    prompt = f"Question: {question}\n\nRules:\n{rules_block}"

    try:
        answer_text = generate_answer(prompt)
    except errors.APIError:
        return Response(
            {"error": "The language model could not be reached."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if not answer_text:
        return Response(
            {"error": "The language model returned an empty response."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    return Response({"answer": [{"type": "text", "text": answer_text}]})