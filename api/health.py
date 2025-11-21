"""
Health check endpoint for Life Story Game AI Interviewer.

Simple health check to verify serverless functions are operational.

Endpoint: GET /api/health
"""

import json
from datetime import datetime


def handler(request):
    """
    Vercel serverless function handler for health check endpoint.

    Returns:
    {
        "status": "ok",
        "service": "Life Story Game AI Interviewer",
        "timestamp": "2025-11-21T12:00:00Z"
    }
    """
    # Handle CORS preflight
    if request.get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": "",
        }

    # Accept any HTTP method for health check
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(
            {
                "status": "ok",
                "service": "Life Story Game AI Interviewer",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        ),
    }
