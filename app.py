from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
from flask_cors import CORS  # Add this for CORS support

app = Flask(__name__)
CORS(app)  # Allow requests from your Hostinger domain

print("✅ Peppol Proxy Service Starting...")

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Peppol Proxy Service</title></head>
    <body>
        <h1>✅ Peppol Proxy Service is Running!</h1>
        <p>Endpoints:</p>
        <ul>
            <li><strong>GET /health</strong> - Health check</li>
            <li><strong>POST /send</strong> - Send invoice to Peppol</li>
            <li><strong>GET /send</strong> - Test endpoint (returns info)</li>
        </ul>
        <p>Use POST request to /send with JSON data:</p>
        <pre>
{
    "invoice_number": "INV-001",
    "supplier_vat": "BE123456789",
    "customer_vat": "BE987654321",
    "amount": "100.00"
}
        </pre>
    </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway"""
    return jsonify({
        "service": "peppol-proxy",
        "status": "healthy",
        "time": datetime.now().isoformat()
    })

@app.route('/send', methods=['GET', 'POST'])  # Allow both GET and POST
def send_invoice():
    """Handle invoice sending - accepts both GET (test) and POST (real)"""
    
    if request.method == 'GET':
        # Return info for GET requests (testing)
        return jsonify({
            "message": "Peppol Send Endpoint",
            "instructions": "Send POST request with JSON invoice data",
            "required_fields": {
                "invoice_number": "string",
                "supplier_vat": "BEXXXXXXXXX",
                "customer_vat": "BEXXXXXXXXX",
                "amount": "number"
            },
            "example": {
                "invoice_number": "INV-2024-001",
                "supplier_vat": "BE123456789",
                "customer_vat": "BE987654321",
                "amount": 100.00
            }
        })
    
    elif request.method == 'POST':
        # Handle POST request from Hostinger form
        try:
            # Get JSON data
            if not request.is_json:
                return jsonify({
                    "success": False,
                    "error": "Content-Type must be application/json"
                }), 400
            
            data = request.get_json()
            print(f"📨 Received invoice: {data.get('invoice_number', 'Unknown')}")
            
            # Validate required fields
            required = ['invoice_number', 'supplier_vat', 'customer_vat', 'amount']
            for field in required:
                if field not in data:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }), 400
            
            # Generate UBL XML
            ubl_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>{data['invoice_number']}</cbc:ID>
  <cbc:IssueDate>{datetime.now().strftime('%Y-%m-%d')}</cbc:IssueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  
  <!-- Belgian Supplier -->
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyIdentification>
        <cbc:ID schemeID="0190">{data['supplier_vat'].replace('BE', '')}</cbc:ID>
      </cac:PartyIdentification>
      <cac:PartyName>
        <cbc:Name>{data.get('supplier_name', 'Supplier')}</cbc:Name>
      </cac:PartyName>
    </cac:Party>
  </cac:AccountingSupplierParty>
  
  <!-- Belgian Customer -->
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyIdentification>
        <cbc:ID schemeID="0190">{data['customer_vat'].replace('BE', '')}</cbc:ID>
      </cac:PartyIdentification>
    </cac:Party>
  </cac:AccountingCustomerParty>
  
  <!-- Totals -->
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="EUR">{data['amount']}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="EUR">{data['amount']}</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="EUR">{float(data['amount']) * 1.21}</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="EUR">{float(data['amount']) * 1.21}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>'''
            
            # Send to free Peppol test endpoint
            print("📤 Sending to Peppol test endpoint...")
            response = requests.post(
                'https://test-ap.peppol.eu/inbound',
                data=ubl_xml,
                headers={'Content-Type': 'application/xml'},
                timeout=10
            )
            
            print(f"✅ Peppol response: {response.status_code}")
            
            # Return success
            return jsonify({
                "success": True,
                "message": "Invoice sent via Peppol (Test Mode)",
                "invoice_number": data['invoice_number'],
                "supplier_vat": data['supplier_vat'],
                "customer_vat": data['customer_vat'],
                "amount": data['amount'],
                "peppol_response": response.status_code,
                "cost": "€0.00",
                "test_mode": True,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e),
                "message": "Failed to process invoice"
            }), 500

@app.route('/test', methods=['GET'])
def test():
    """Simple test endpoint"""
    return jsonify({
        "status": "active",
        "service": "Peppol Proxy",
        "version": "1.0"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
