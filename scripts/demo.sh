#!/bin/bash
# I have done this script using ai, because i didn't use curl to test
# Also I have made a test using postman requests, you can see it in docs/ folder
BASE_URL="http://127.0.0.1:8000"

EMAIL_A="usera@example.com"
PASSWORD_A="Password123!"

EMAIL_B="userb@example.com"
PASSWORD_B="Password123!"


echo "=========================================="
echo "1. Register User A"
echo "=========================================="

curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL_A\",
    \"password\": \"$PASSWORD_A\"
  }"

echo
echo


echo "=========================================="
echo "2. Register User B"
echo "=========================================="

curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL_B\",
    \"password\": \"$PASSWORD_B\"
  }"

echo
echo


echo "=========================================="
echo "3. Login User A"
echo "=========================================="

LOGIN_A=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL_A\",
    \"password\": \"$PASSWORD_A\"
  }")

echo "$LOGIN_A"

TOKEN_A=$(echo "$LOGIN_A" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo
echo "User A token:"
echo "$TOKEN_A"

echo
echo


echo "=========================================="
echo "4. Login User B"
echo "=========================================="

LOGIN_B=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL_B\",
    \"password\": \"$PASSWORD_B\"
  }")

echo "$LOGIN_B"

TOKEN_B=$(echo "$LOGIN_B" | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo
echo


echo "=========================================="
echo "5. User A creates a note"
echo "=========================================="

CREATE_NOTE=$(curl -s -X POST "$BASE_URL/notes" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Acceptance Test Note",
    "body_markdown": "# Version 1\n<script>alert(1)</script>\nThis are incorrect.",
    "folder_id": null
  }')

echo "$CREATE_NOTE"

NOTE_ID=$(echo "$CREATE_NOTE" | python -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo
echo "Created note ID: $NOTE_ID"

echo
echo


echo "=========================================="
echo "6. User A updates note"
echo "=========================================="

curl -s -X PATCH "$BASE_URL/notes/$NOTE_ID" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Acceptance Test Note Updated",
    "body_markdown": "# Version 2\n<script>alert(2)</script>\nThis are still incorrect."
  }'

echo
echo


echo "=========================================="
echo "7. Get revisions"
echo "Expected: 2 revisions"
echo "=========================================="

REVISIONS=$(curl -s -X GET "$BASE_URL/notes/$NOTE_ID/revisions" \
  -H "Authorization: Bearer $TOKEN_A")

echo "$REVISIONS"

REVISION_1_ID=$(echo "$REVISIONS" | python -c "
import sys, json
data = json.load(sys.stdin)
for rev in data:
    if rev['revision_number'] == 1:
        print(rev['id'])
        break
")

echo
echo "Revision 1 ID: $REVISION_1_ID"

echo
echo


echo "=========================================="
echo "8. Restore revision 1"
echo "Expected: new revision is created"
echo "=========================================="

curl -s -X POST \
  "$BASE_URL/notes/$NOTE_ID/revisions/$REVISION_1_ID/restore" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "9. Get revisions again"
echo "Expected: 3 revisions"
echo "=========================================="

curl -s -X GET "$BASE_URL/notes/$NOTE_ID/revisions" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "10. Soft delete note"
echo "=========================================="

curl -i -X DELETE "$BASE_URL/notes/$NOTE_ID" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "11. GET /notes"
echo "Expected: deleted note NOT present"
echo "=========================================="

curl -s -X GET "$BASE_URL/notes" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "12. GET /notes/trash"
echo "Expected: deleted note present"
echo "=========================================="

curl -s -X GET "$BASE_URL/notes/trash" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "13. Restore deleted note"
echo "=========================================="

curl -s -X POST "$BASE_URL/notes/$NOTE_ID/restore" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "14. User B requests User A note"
echo "Expected: 404"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID" \
  -H "Authorization: Bearer $TOKEN_B"

echo
echo


echo "=========================================="
echo "15. Render note as HTML"
echo "Expected: script removed/sanitized"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: text/html"

echo
echo


echo "=========================================="
echo "16. Render note as Markdown"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: text/markdown"

echo
echo


echo "=========================================="
echo "17. Render note as JSON"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: application/json"

echo
echo


echo "=========================================="
echo "18. Get ETag"
echo "=========================================="

HEADERS=$(curl -s -D - -o /dev/null \
  -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: text/html")

echo "$HEADERS"

ETAG=$(echo "$HEADERS" | grep -i "^etag:" | sed 's/[Ee][Tt][Aa][Gg]: //' | tr -d '\r')

echo
echo "ETag: $ETAG"

echo
echo


echo "=========================================="
echo "19. Render using If-None-Match"
echo "Expected: 304"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: text/html" \
  -H "If-None-Match: $ETAG"

echo
echo


echo "=========================================="
echo "20. Unsupported Accept"
echo "Expected: 406"
echo "=========================================="

curl -i -X GET "$BASE_URL/notes/$NOTE_ID/render" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Accept: application/xml"

echo
echo


echo "=========================================="
echo "21. Get latest revision"
echo "=========================================="

LATEST_REVISIONS=$(curl -s -X GET \
  "$BASE_URL/notes/$NOTE_ID/revisions" \
  -H "Authorization: Bearer $TOKEN_A")

echo "$LATEST_REVISIONS"

LATEST_REVISION_ID=$(echo "$LATEST_REVISIONS" | python -c "
import sys, json
data = json.load(sys.stdin)
print(data[0]['id'])
")

echo
echo "Latest revision ID: $LATEST_REVISION_ID"

echo
echo


echo "=========================================="
echo "22. Grammar check latest revision"
echo "=========================================="

curl -s -X POST \
  "$BASE_URL/notes/$NOTE_ID/revisions/$LATEST_REVISION_ID/grammar-check" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "23. Get persisted grammar issues"
echo "=========================================="

curl -s -X GET \
  "$BASE_URL/notes/$NOTE_ID/revisions/$LATEST_REVISION_ID/grammar-issues" \
  -H "Authorization: Bearer $TOKEN_A"

echo
echo


echo "=========================================="
echo "DEMO FINISHED"
echo "=========================================="