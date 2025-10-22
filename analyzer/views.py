from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.http import Http404
import hashlib
from collections import Counter

DB = {}  # in-memory database

def analyze_string(value):
    value_lower = value.lower()
    sha256_hash = hashlib.sha256(value.encode()).hexdigest()
    return {
        "length": len(value),
        "is_palindrome": value_lower == value_lower[::-1],
        "unique_characters": len(set(value)),
        "word_count": len(value.split()),
        "sha256_hash": sha256_hash,
        "character_frequency_map": dict(Counter(value))
    }

class StringListCreateAPIView(APIView):
    def get(self, request):
        data = [{"id": item["properties"]["sha256_hash"],
                 "value": item["value"],
                 "properties": item["properties"],
                 "created_at": item["created_at"]} for item in DB.values()]
        return Response({"data": data, "count": len(data)})

    def post(self, request):
        value = request.data.get("value")
        if value is None:
            return Response({"detail": "Missing 'value' field"}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(value, str):
            return Response({"detail": "'value' must be a string"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        sha256_hash = hashlib.sha256(value.encode()).hexdigest()
        if sha256_hash in DB:
            return Response({"detail": "String already exists"}, status=status.HTTP_409_CONFLICT)
        properties = analyze_string(value)
        DB[sha256_hash] = {
            "value": value,
            "properties": properties,
            "created_at": timezone.now()
        }
        return Response({
            "id": sha256_hash,
            "value": value,
            "properties": properties,
            "created_at": DB[sha256_hash]["created_at"]
        }, status=status.HTTP_201_CREATED)

class StringDetailAPIView(APIView):
    def get_object(self, value):
        sha256_hash = hashlib.sha256(value.encode()).hexdigest()
        if sha256_hash not in DB:
            raise Http404
        return DB[sha256_hash]

    def get(self, request, value):
        obj = self.get_object(value)
        return Response({
            "id": obj["properties"]["sha256_hash"],
            "value": obj["value"],
            "properties": obj["properties"],
            "created_at": obj["created_at"]
        })

    def delete(self, request, value):
        sha256_hash = hashlib.sha256(value.encode()).hexdigest()
        if sha256_hash not in DB:
            raise Http404
        del DB[sha256_hash]
        return Response(status=status.HTTP_204_NO_CONTENT)

class NLFilterAPIView(APIView):
    def get(self, request):
        query = request.query_params.get("query")
        if not query:
            return Response({"detail": "Missing query parameter"}, status=status.HTTP_400_BAD_REQUEST)
        filters = {}
        query_lower = query.lower()
        if "palindromic" in query_lower:
            filters["is_palindrome"] = True
        if "single word" in query_lower:
            filters["word_count"] = 1
        results = []
        for item in DB.values():
            match = True
            if "is_palindrome" in filters and item["properties"]["is_palindrome"] != filters["is_palindrome"]:
                match = False
            if "word_count" in filters and item["properties"]["word_count"] != filters["word_count"]:
                match = False
            if match:
                results.append({
                    "id": item["properties"]["sha256_hash"],
                    "value": item["value"],
                    "properties": item["properties"],
                    "created_at": item["created_at"]
                })
        return Response({
            "data": results,
            "count": len(results),
            "interpreted_query": {
                "original": query,
                "parsed_filters": filters
            }
        })
