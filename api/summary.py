import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.ai_fallback import generate_summary


class handler(BaseHTTPRequestHandler):
    """
    Vercel serverless function handler for summary endpoint.

    Endpoint: POST /api/summary

    Request Body:
        - messages: Array of conversation messages (required)
        - phases: Array of phase identifiers to summarize (optional)
                  e.g., ["CHILDHOOD", "ADOLESCENCE"]

    Response:
        - summary: The generated summary text
        - phases_summarized: Array of phases that were summarized (if phases provided)
    """

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(body) if body else {}

            messages = data.get("messages", [])
            phases = data.get("phases", None)

            if not messages:
                self._send_json_response(400, {"error": "Messages required"})
                return

            # Validate phases if provided
            if phases is not None:
                if not isinstance(phases, list):
                    self._send_json_response(400, {"error": "phases must be an array"})
                    return
                if not all(isinstance(p, str) for p in phases):
                    self._send_json_response(
                        400, {"error": "All phases must be strings"}
                    )
                    return

            # Generate summary with optional phases filtering
            result = generate_summary(messages=messages, phases=phases)

            if not result["success"]:
                self._send_json_response(500, {"error": result["error"]})
                return

            response_data = {"summary": result["content"]}

            # Include phases_summarized if phases were provided
            if result.get("phases_summarized"):
                response_data["phases_summarized"] = result["phases_summarized"]

            self._send_json_response(200, response_data)

        except Exception as e:
            print(f"[ERROR] Summary generation failed: {e}")
            self._send_json_response(500, {"error": str(e)})

    def _send_json_response(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
