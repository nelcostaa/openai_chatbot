#!/usr/bin/env python3
"""
Local development server that simulates Vercel serverless functions.
Run this alongside 'npm run dev' in the frontend directory.
"""

import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from api.chat import handler as chat_handler
from api.health import handler as health_handler
from api.model_status import handler as model_status_handler

app = Flask(__name__)
CORS(app)


def vercel_request(flask_req):
    """Convert Flask request to Vercel format."""
    body = flask_req.get_data(as_text=True)
    if body:
        try:
            body = json.loads(body)
        except:
            pass

    return {
        "method": flask_req.method,
        "body": body,
        "headers": dict(flask_req.headers),
        "query": dict(flask_req.args),
    }


def vercel_response(result):
    """Convert Vercel response to Flask format."""
    body = result.get("body", "")
    if isinstance(body, str) and body:
        try:
            body = json.loads(body)
        except:
            pass

    return jsonify(body) if isinstance(body, dict) else body, result.get(
        "statusCode", 200
    )


@app.route("/api/health", methods=["GET", "OPTIONS"])
def health():
    result = health_handler(vercel_request(request))
    return vercel_response(result)


@app.route("/api/model-status", methods=["GET", "OPTIONS"])
def model_status():
    result = model_status_handler(vercel_request(request))
    return vercel_response(result)


@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    result = chat_handler(vercel_request(request))
    return vercel_response(result)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Local Development Server Running")
    print("=" * 60)
    print(f"\n📡 API Server: http://localhost:5000")
    print(f"🎨 Frontend:   cd frontend && npm run dev")
    print(f"\n✅ Endpoints:")
    print(f"   GET  http://localhost:5000/api/health")
    print(f"   GET  http://localhost:5000/api/model-status")
    print(f"   POST http://localhost:5000/api/chat")
    print(f"\n💡 Configure frontend to proxy /api/* to http://localhost:5000\n")

    app.run(debug=True, port=5000, host="0.0.0.0")
