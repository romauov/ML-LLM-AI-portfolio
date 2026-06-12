#!/bin/bash
# Test script for VetRetro API endpoints

BASE_URL="http://localhost:8000"

echo "=== Testing VetRetro API ==="
echo ""

echo "1. Health check:"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

echo "2. List models:"
curl -s "$BASE_URL/v1/models" | python3 -m json.tool
echo ""

echo "3. List investigations:"
curl -s "$BASE_URL/api/investigations/list" | python3 -m json.tool | head -30
echo ""

echo "4. Chat completion (non-streaming):"
curl -s -X POST "$BASE_URL/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "investigations-swine",
    "messages": [
      {"role": "user", "content": "What is ETEC? Answer in 1-2 sentences."}
    ],
    "stream": false
  }' | python3 -m json.tool
echo ""

echo "5. Create investigation:"
curl -s -X POST "$BASE_URL/api/investigations/create" \
  -H "Content-Type: application/json" \
  -d '{
    "farm_name": "api_test",
    "problem_type": "test",
    "description": "API test investigation"
  }' | python3 -m json.tool
echo ""

echo "=== All tests completed ==="
