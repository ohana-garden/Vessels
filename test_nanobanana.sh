#!/bin/bash
# Test NanoBanana API directly
# Run: ./test_nanobanana.sh

API_KEY="${NANOBANANA_API_KEY:-734e2ae0b4ce8ff06d5ccfed5d9deca4}"

echo "Testing NanoBanana API..."
echo "API Key: ${API_KEY:0:8}...${API_KEY: -4}"
echo ""

curl --request POST \
  --url https://api.nanobananaapi.ai/api/v1/nanobanana/generate \
  --header "Authorization: Bearer $API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
  "prompt": "A warm Hawaiian community scene with kupuna teaching keiki in a taro garden. Style: warm, Hawaiian, community-focused",
  "numImages": 1,
  "type": "TEXTTOIAMGE",
  "image_size": "16:9"
}' | python3 -m json.tool

echo ""
echo "Done. If you got a taskId, poll with:"
echo "curl -H \"Authorization: Bearer $API_KEY\" \"https://api.nanobananaapi.ai/api/v1/nanobanana/record-info?taskId=YOUR_TASK_ID\""
