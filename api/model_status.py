"""
Model status endpoint for Life Story Game AI Interviewer.

Returns information about available Gemini models and fallback configuration.

Endpoint: GET /api/model-status
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.ai_fallback import get_model_cascade


def handler(request):
    """
    Vercel serverless function handler for model status endpoint.

    Returns:
    {
        "available_models": ["gemini-2.5-flash", ...],
        "total_models": 6,
        "fallback_enabled": true,
        "source": "environment|default"
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

    # Only accept GET
    if request.get("method") != "GET":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed. Use GET."}),
        }

    try:
        # Get model cascade from environment or defaults
        import os

        models = get_model_cascade()
        env_models = os.getenv("GEMINI_MODELS")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                {
                    "available_models": models,
                    "total_models": len(models),
                    "fallback_enabled": True,
                    "source": "environment" if env_models else "default",
                }
            ),
        }

    except Exception as e:
        print(f"[ERROR] Error in model_status handler: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Internal server error: {str(e)}"}),
        }
