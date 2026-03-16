"""
Aegis-AI Threat Analyzer
========================
Purpose: AI-powered log classification using LLM intelligence
Author: Aditya Batra

This module:
- Polls database for unclassified logs
- Constructs intelligent prompts for LLM analysis
- Classifies logs as SAFE, SUSPICIOUS, or CRITICAL_THREAT
- Updates database with AI verdicts
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional

from database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAIEngine:
    """
    Fallback mock AI engine for testing without API keys.

    Uses rule-based heuristics to simulate LLM behavior.
    """

    def classify_log(self, log_message: str, log_level: str, source_ip: str) -> Dict[str, Any]:
        """
        Rule-based classification simulating AI analysis.

        Args:
            log_message: The raw log message
            log_level: Log severity level
            source_ip: Source IP address

        Returns:
            Classification result with confidence score
        """
        message_lower = log_message.lower()

        # Critical threat patterns
        critical_patterns = [
            'sql injection', 'union select', 'drop table', 'or 1=1',
            '<script>', 'onerror=', 'javascript:',
            'cat /etc/passwd', '/etc/shadow', 'reverse shell',
            '50+ failed login', 'command injection'
        ]

        # Suspicious patterns
        suspicious_patterns = [
            'failed password', '404', 'admin', 'phpmyadmin',
            'connection attempt', 'rejected', 'blocked',
            '../', 'directory traversal'
        ]

        # Check for critical threats
        for pattern in critical_patterns:
            if pattern in message_lower:
                return {
                    "classification": "CRITICAL_THREAT",
                    "confidence": 0.95,
                    "reasoning": f"Detected {pattern} - indicates active attack",
                    "attack_type": self._identify_attack_type(message_lower)
                }

        # Check for suspicious activity
        for pattern in suspicious_patterns:
            if pattern in message_lower:
                return {
                    "classification": "SUSPICIOUS",
                    "confidence": 0.75,
                    "reasoning": f"Detected {pattern} - warrants investigation",
                    "attack_type": "reconnaissance"
                }

        # Check log level
        if log_level in ['ERROR', 'CRITICAL']:
            return {
                "classification": "SUSPICIOUS",
                "confidence": 0.60,
                "reasoning": f"High severity log level: {log_level}",
                "attack_type": "unknown"
            }

        # Default: SAFE
        return {
            "classification": "SAFE",
            "confidence": 0.90,
            "reasoning": "Normal operational activity",
            "attack_type": None
        }

    def _identify_attack_type(self, message: str) -> str:
        """Identify the specific attack type."""
        if 'sql' in message or 'union' in message or 'select' in message:
            return "SQL_INJECTION"
        elif '<script>' in message or 'xss' in message or 'onerror' in message:
            return "XSS"
        elif 'cat' in message or '/etc/' in message or 'passwd' in message:
            return "COMMAND_INJECTION"
        elif 'failed login' in message or 'failed password' in message:
            return "BRUTE_FORCE"
        elif '../' in message or 'directory traversal' in message:
            return "PATH_TRAVERSAL"
        else:
            return "UNKNOWN_THREAT"


class OpenAIEngine:
    """
    OpenAI GPT-based threat analysis engine.
    """

    def __init__(self, api_key: str):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4o-mini"  # Cost-effective model for classification
            logger.info("✅ OpenAI engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI: {e}")
            raise

    def classify_log(self, log_message: str, log_level: str, source_ip: str) -> Dict[str, Any]:
        """
        Use OpenAI GPT to classify the log entry.

        Args:
            log_message: The raw log message
            log_level: Log severity level
            source_ip: Source IP address

        Returns:
            Classification result from GPT
        """
        prompt = self._construct_prompt(log_message, log_level, source_ip)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert specializing in log analysis and threat detection. Analyze logs and classify them accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()
            return self._parse_ai_response(result_text)

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock engine
            return MockAIEngine().classify_log(log_message, log_level, source_ip)

    def _construct_prompt(self, log_message: str, log_level: str, source_ip: str) -> str:
        """Construct the classification prompt."""
        return f"""Analyze this server log and classify it as one of: SAFE, SUSPICIOUS, or CRITICAL_THREAT.

Log Details:
- Level: {log_level}
- Source IP: {source_ip}
- Message: {log_message}

Classification Criteria:
- SAFE: Normal operational activity, legitimate user actions
- SUSPICIOUS: Reconnaissance, probing, failed attempts, unusual patterns
- CRITICAL_THREAT: Active attacks (SQLi, XSS, command injection, brute force, RCE)

Respond in JSON format:
{{
    "classification": "SAFE|SUSPICIOUS|CRITICAL_THREAT",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "attack_type": "SQL_INJECTION|XSS|BRUTE_FORCE|etc or null"
}}"""

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            # Try to extract JSON from response
            if '{' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Default safe classification on parse error
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "Parse error - defaulting to safe",
                "attack_type": None
            }


class AnthropicEngine:
    """
    Anthropic Claude-based threat analysis engine.
    """

    def __init__(self, api_key: str):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-haiku-20241022"  # Fast and cost-effective
            logger.info("✅ Anthropic engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic: {e}")
            raise

    def classify_log(self, log_message: str, log_level: str, source_ip: str) -> Dict[str, Any]:
        """
        Use Claude to classify the log entry.

        Args:
            log_message: The raw log message
            log_level: Log severity level
            source_ip: Source IP address

        Returns:
            Classification result from Claude
        """
        prompt = self._construct_prompt(log_message, log_level, source_ip)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            result_text = response.content[0].text
            return self._parse_ai_response(result_text)

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            # Fallback to mock engine
            return MockAIEngine().classify_log(log_message, log_level, source_ip)

    def _construct_prompt(self, log_message: str, log_level: str, source_ip: str) -> str:
        """Construct the classification prompt."""
        return f"""You are a cybersecurity expert. Analyze this server log and classify it.

Log Details:
- Level: {log_level}
- Source IP: {source_ip}
- Message: {log_message}

Classify as: SAFE, SUSPICIOUS, or CRITICAL_THREAT

Respond ONLY with valid JSON:
{{
    "classification": "SAFE|SUSPICIOUS|CRITICAL_THREAT",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "attack_type": "SQL_INJECTION|XSS|BRUTE_FORCE|etc or null"
}}"""

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate the AI response."""
        try:
            if '{' in response_text:
                json_start = response_text.index('{')
                json_end = response_text.rindex('}') + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "classification": "SAFE",
                "confidence": 0.5,
                "reasoning": "Parse error",
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
        self.ai_engine = self._initialize_ai_engine()

    def _initialize_ai_engine(self):
        """
        Initialize the AI engine with priority: OpenAI > Anthropic > Mock.

        Returns:
            Initialized AI engine instance
        """
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Try OpenAI first
        if openai_key and openai_key != "mock" and openai_key.startswith("sk-"):
            try:
                logger.info("🤖 Attempting to initialize OpenAI engine...")
                return OpenAIEngine(openai_key)
            except Exception as e:
                logger.warning(f"OpenAI initialization failed: {e}")

        # Try Anthropic second
        if anthropic_key and anthropic_key != "mock" and anthropic_key.startswith("sk-ant-"):
            try:
                logger.info("🤖 Attempting to initialize Anthropic engine...")
                return AnthropicEngine(anthropic_key)
            except Exception as e:
                logger.warning(f"Anthropic initialization failed: {e}")

        # Fallback to mock
        logger.warning("⚠️  No valid API keys found - using Mock AI Engine")
        logger.info("💡 To use real AI: Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        return MockAIEngine()

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

                status_emoji = "🚨" if classification == "CRITICAL_THREAT" else "⚠️" if classification == "SUSPICIOUS" else "✅"
                logger.info(f"{status_emoji} Log {log['id']}: {classification}")

            except Exception as e:
                logger.error(f"❌ Failed to analyze log {log['id']}: {e}")

    def run(self, interval: int = 5):
        """
        Continuous analysis loop.

        Args:
            interval: Seconds to wait between batch analyses
        """
        logger.info(f"🚀 Threat Analyzer started - analyzing every {interval}s")

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
    analyzer = ThreatAnalyzer(db)
    interval = int(os.getenv("ANALYSIS_INTERVAL", 5))
    analyzer.run(interval=interval)


if __name__ == "__main__":
    main()
