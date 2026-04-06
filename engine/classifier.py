"""Claude-powered geopolitical event classifier."""

import json
import os
from typing import Dict, Optional
from pathlib import Path
from anthropic import Anthropic
from anthropic import AuthenticationError, APIError

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass


class EventClassifier:
    """Classifies geopolitical events into trade signals using Claude."""

    def __init__(self, model: str = "claude-opus-4-6"):
        """Initialize Claude client."""
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build the classification system prompt."""
        return """You are an expert geopolitical event analyst and forex trader. 
Your job is to classify geopolitical events into trade signals.

For each event, respond with ONLY valid JSON (no markdown, no explanations):
{
    "action": "BUY" | "SELL" | "HOLD",
    "symbol": "EURUSD" | "GBPUSD" | "USDJPY" | "AUDUSD" | "USDCAD" | "XAUUSD" | "XBRUSD" | "XTIUSD" | "HOLD",
    "confidence": 0.0-1.0,
    "rationale": "Brief explanation of why this event triggers this signal"
}

Rules:
1. If the event is not trading-relevant, return HOLD with confidence 0.1-0.3
2. If event strongly affects commodity/currency, return BUY/SELL with confidence 0.6-0.9
3. Symbol should match the most directly impacted asset:
   - Fed rate hike → USD strength → EURUSD SELL (or USDJPY BUY if JPY weakness)
   - Oil production cuts → XBRUSD/XTIUSD BUY
   - Geopolitical tensions → XAUUSD (gold) BUY
   - China economic data → AUDUSD (Aussie commodity currency) direction
4. Always return valid JSON only, never wrap in markdown code blocks
5. Confidence = your certainty that this signal will be profitable (0.0 = totally unsure, 1.0 = 100% confident)
"""

    def _get_fallback_signal(self, event: Dict, error_type: str = "general") -> Dict:
        """
        Generate a fallback signal based on event severity.
        Used when Claude API is unavailable.
        """
        severity = event.get("severity", "low")
        
        # For critical events, return a buy gold signal as fallback
        if severity == "critical":
            return {
                "action": "BUY",
                "symbol": "XAUUSD",
                "confidence": 0.65,
                "rationale": "Critical event detected - gold hedge recommended"
            }
        
        # Default fallback for any error
        return {
            "action": "HOLD",
            "symbol": "HOLD",
            "confidence": 0.0,
            "rationale": f"Classifier error: {error_type}"
        }

    def classify(self, event: Dict) -> Dict:
        """
        Classify a geopolitical event into a trade signal.

        Args:
            event: Dict with keys: id, title, description, severity (low/medium/high/critical)

        Returns:
            Dict with keys: action, symbol, confidence, rationale
        """
        event_text = f"""
Event ID: {event.get('id')}
Title: {event.get('title')}
Description: {event.get('description')}
Severity: {event.get('severity', 'medium')}
"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": event_text}
                ]
            )

            response_text = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            signal = json.loads(response_text)

            # Validate response structure
            assert isinstance(signal.get("confidence"), (int, float))
            assert 0 <= signal["confidence"] <= 1.0
            assert signal.get("action") in ["BUY", "SELL", "HOLD"]
            assert isinstance(signal.get("rationale"), str)
            assert len(signal["rationale"]) > 0

            return signal

        except (json.JSONDecodeError, AssertionError, KeyError) as e:
            # Fallback: treat parsing error as low-confidence HOLD
            return {
                "action": "HOLD",
                "symbol": "HOLD",
                "confidence": 0.0,
                "rationale": f"Classifier error: {str(e)}"
            }
        except (AuthenticationError, APIError) as e:
            # Handle authentication and API errors gracefully
            # For critical events, still recommend a trade; otherwise HOLD
            return self._get_fallback_signal(event, "API error")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")
