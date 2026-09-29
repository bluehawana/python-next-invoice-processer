#!/bin/bash
# Upload handwritten data to invoices.bluehawana.com

API_URL="https://invoices.bluehawana.com"

echo "=========================================="
echo "Uploading to invoices.bluehawana.com"
echo "=========================================="

# Option 1: Upload handwritten photo (if you have it)
if [ -f "$1" ]; then
    echo "📸 Uploading handwritten photo: $1"
    curl -X POST "$API_URL/upload-paper" \
      -F "file=@$1" \
      -H "Content-Type: multipart/form-data"
    echo ""
    echo "✅ Photo uploaded! Check the website for results."
else
    # Option 2: Manual input (if no photo)
    echo "📝 Sending manual handwritten data for August 2026..."
    
    curl -X POST "$API_URL/upload-handwritten-manual" \
      -H "Content-Type: application/json" \
      -d '{
        "records": {
          "Wolt": [598.23, 112.86],
          "Uber": [677.95, 3075.15, 2904.20],
          "Foodora": [20615.75, 2716.65, 9602.19, 13304.28],
          "Stripe": [962.68, 748.12, 728.42, 2058.34, 2261.02, 1012.20, 1035.04, 1156.13, 1257.56, 1018.67, 1133.82, 982.27, 1256.26, 1451.38, 1348.42, 651.80]
        }
      }'
    
    echo ""
    echo "✅ Manual data uploaded!"
fi

echo ""
echo "=========================================="
echo "Now run monthly sync on VPS..."
echo "=========================================="

# Trigger monthly sync for August 2026
echo "🔄 Running monthly sync..."
curl -X POST "$API_URL/monthly-sync" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 8}'

echo ""
echo "✅ Done! Check https://invoices.bluehawana.com"
