from flask import Flask, jsonify
from datetime import datetime
import os

app = Flask(__name__)

print("✅ Starting Peppol Proxy...")

@app.route('/')
def home():
    return '''
    <h1>Peppol Proxy is Working!</h1>
    <p>✅ Service is running correctly.</p>
    <p><a href="/health">Health Check</a></p>
    <p><a href="/test">Test Endpoint</a></p>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "peppol-proxy",
        "time": datetime.now().isoformat()
    })

@app.route('/test')
def test():
    return jsonify({
        "message": "All systems go!",
        "next": "POST to /send to send invoices"
    })

@app.route('/send', methods=['POST'])
def send():
    return jsonify({
        "success": True,
        "message": "Invoice would be sent here",
        "cost": "0€"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Running on port {port}")
    app.run(host='0.0.0.0', port=port)