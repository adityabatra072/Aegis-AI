"""
Aegis-AI Threat Analyzer
========================
Purpose: AI-powered log classification using any OpenAI-compatible API
Author: Aditya Batra

This module:
- Polls database for unclassified logs
- Constructs intelligent prompts for LLM analysis
- Classifies logs as SAFE, SUSPICIOUS, or CRITICAL_THREAT
- Updates database with AI verdicts

Supports: OpenAI, Anthropic, LiteLLM, and any OpenAI-compatible API endpoint
"""

import os
import time
import json
import logging
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from database import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIEngine:
    """
    Universal AI engine supporting any OpenAI-compatible API.

    Compatible with:
    - OpenAI API (gpt-4, gpt-4o-mini, etc.)
    - Anthropic API via OpenAI compatibility layer
    - LiteLLM proxy
    - Azure OpenAI
    - LocalAI
    - Any other OpenAI-compatible endpoint
    """

    def __init__(self):
        """Initialize AI engine with environment configuration."""
        self.base_url = os.getenv("AI_BASE_URL")
        self.api_key = os.getenv("AI_API_KEY")
        self.model = os.getenv("AI_MODEL")

        # Validate configuration
        if not self.base_url or not self.api_key or not self.model:
            raise ValueError(
                "❌ AI configuration missing! Set AI_BASE_URL, AI_API_KEY, and AI_MODEL in .env file"
            )

        # Ensure base_url ends with /v1 for OpenAI compatibility
        if not self.base_url.endswith('/v1'):
            self.base_url = f"{self.base_url}/v1"

        self.endpoint = f"{self.base_url}/chat/completions"

        logger.info(f"✅ AI engine initialized")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   Model: {self.model}")

    def classify_log(self, log_message: str, log_level: str, source_ip: str) -> Dict[str, Any]:
        """
        Use AI to classify the log entry.

        Args:
            log_message: The raw log message
            log_level: Log severity level
            source_ip: Source IP address

        Returns:
            Classification result from AI
        """
        prompt = self._construct_prompt(log_message, log_level, source_ip)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a cybersecurity expert specializing in log analysis and threat detection. Analyze logs and classify them accurately. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Low temperature for consistent classification
            "max_tokens": 300
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                result_text = data['choices'][0]['message']['content'].strip()
                return self._parse_ai_response(result_text)
            else:
                logger.error(f"AI API error: {response.status_code} - {response.text}")
                # Return safe classification on error
                return {
                    "classification": "SAFE",
                    "confidence": 0.5,
                    "reasoning": f"API error (status {response.status_code}), defaulting to safe",
                    "attack_type": None
                }

        except requests.exceptions.Timeout:
            logger.error("AI API timeout")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "API timeout, defaulting to safe",
                "attack_type": None
            }
        except Exception as e:
            logger.error(f"AI API exception: {e}")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": f"Exception: {str(e)}, defaulting to safe",
                "attack_type": None
            }

    def _construct_prompt(self, log_message: str, log_level: str, source_ip: str) -> str:
        """Construct the classification prompt for the AI."""
        return f"""Analyze this server log and classify it as one of: SAFE, SUSPICIOUS, or CRITICAL_THREAT.

Log Details:
- Level: {log_level}
- Source IP: {source_ip}
- Message: {log_message}

Classification Criteria:
- SAFE: Normal operational activity, legitimate user actions
- SUSPICIOUS: Reconnaissance, probing, failed attempts, unusual patterns
- CRITICAL_THREAT: Active attacks (SQLi, XSS, command injection, brute force, RCE)

Respond ONLY with valid JSON in this exact format:
{{
    "classification": "SAFE|SUSPICIOUS|CRITICAL_THREAT",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "attack_type": "SQL_INJECTION|XSS|BRUTE_FORCE|COMMAND_INJECTION|PATH_TRAVERSAL|null"
}}"""

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            # Extract JSON from response
            if '{' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_str = response_text[json_start:json_end]

                # Remove markdown code blocks if present
                json_str = json_str.replace('```json', '').replace('```', '').strip()

                result = json.loads(json_str)

                # Validate required fields
                required_fields = ['classification', 'confidence', 'reasoning']
                if all(field in result for field in required_fields):
                    # Ensure classification is valid
                    valid_classifications = ['SAFE', 'SUSPICIOUS', 'CRITICAL_THREAT']
                    if result['classification'] in valid_classifications:
                        return result

            # If parsing fails, default to safe
            logger.warning(f"Failed to parse AI response: {response_text[:100]}")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "Parse error - defaulting to safe",
                "attack_type": None
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "JSON parse error",
                "attack_type": None
            }
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "Unexpected error",
                "attack_type": None
            }


class ThreatAnalyzer:
    """
    Main analyzer service that orchestrates log classification.
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the threat analyzer.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.ai_engine = AIEngine()

    def analyze_batch(self, batch_size: int = 10):
        """
        Fetch and analyze a batch of unclassified logs.

        Args:
            batch_size: Number of logs to process in one batch
        """
        # Fetch unclassified logs
        logs = self.db.get_unclassified_logs(limit=batch_size)

        if not logs:
            logger.debug("No unclassified logs found")
            return

        logger.info(f"🔍 Analyzing {len(logs)} unclassified logs...")

        for log in logs:
            try:
                # Classify using AI
                result = self.ai_engine.classify_log(
                    log_message=log['message'],
                    log_level=log['log_level'],
                    source_ip=log['source_ip']
                )

                classification = result['classification']
                is_threat = classification in ['SUSPICIOUS', 'CRITICAL_THREAT']

                # Update database
                self.db.update_classification(
                    log_id=log['id'],
                    classification=classification,
                    is_threat=is_threat,
                    metadata={
                        'confidence': result.get('confidence', 0.0),
                        'reasoning': result.get('reasoning', ''),
                        'attack_type': result.get('attack_type')
                    }
                )

                # Log result with appropriate emoji
                if classification == "CRITICAL_THREAT":
                    status_emoji = "🚨"
                elif classification == "SUSPICIOUS":
                    status_emoji = "⚠️"
                else:
                    status_emoji = "✅"

                logger.info(f"{status_emoji} Log {log['id']}: {classification} (confidence: {result.get('confidence', 0):.2f})")

            except Exception as e:
                logger.error(f"❌ Failed to analyze log {log['id']}: {e}")

    def run(self, interval: int = 5):
        """
        Continuous analysis loop.

        Args:
            interval: Seconds to wait between batch analyses
        """
        logger.info(f"🚀 Threat Analyzer started - analyzing every {interval}s")
        logger.info(f"🤖 Using AI model: {self.ai_engine.model}")

        try:
            while True:
                self.analyze_batch(batch_size=10)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Threat Analyzer stopped by user")
        except Exception as e:
            logger.error(f"❌ Threat Analyzer crashed: {e}")
            raise


def main():
    """Entry point for the analyzer service."""
    # Wait for database and log generator to be ready
    logger.info("⏳ Waiting for database connection...")
    time.sleep(10)

    # Initialize database connection
    db = DatabaseManager()

    # Verify connection
    if not db.health_check():
        logger.error("❌ Database health check failed. Exiting.")
        return

    # Start analysis
    try:
        analyzer = ThreatAnalyzer(db)
        interval = int(os.getenv("ANALYSIS_INTERVAL", 5))
        analyzer.run(interval=interval)
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please set AI_BASE_URL, AI_API_KEY, and AI_MODEL in your .env file")
        return


if __name__ == "__main__":
    main()
