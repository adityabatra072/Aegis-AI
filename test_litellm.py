"""
Test script for LiteLLM API connection
"""
import requests
import json
import sys

# Fix Windows encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# LiteLLM configuration
LITELLM_BASE_URL = "http://98.93.50.20"
LITELLM_API_KEY = "sk-uqrquxEL7QgnCU0IoO_tgQ"
MODEL_NAME = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"

def test_litellm_connection():
    """Test basic connection to LiteLLM proxy."""
    print("🧪 Testing LiteLLM API Connection...")
    print(f"   Base URL: {LITELLM_BASE_URL}")
    print(f"   Model: {MODEL_NAME}")

    # Test 1: Simple completion
    url = f"{LITELLM_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {LITELLM_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": "Respond with only 'API connection successful' if you can read this."
            }
        ],
        "max_tokens": 50,
        "temperature": 0.3
    }

    try:
        print("\n📡 Sending test request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"   ✅ Response: {message}")
            return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def test_log_classification():
    """Test log classification with LiteLLM."""
    print("\n🔍 Testing Log Classification...")

    url = f"{LITELLM_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {LITELLM_API_KEY}",
        "Content-Type": "application/json"
    }

    # Test with a SQL injection log
    test_log = "POST /api/login HTTP/1.1 - username=' OR '1'='1-- password=admin"

    prompt = f"""Analyze this server log and classify it as one of: SAFE, SUSPICIOUS, or CRITICAL_THREAT.

Log Details:
- Level: ERROR
- Source IP: 45.142.212.61
- Message: {test_log}

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

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are a cybersecurity expert specializing in log analysis. Respond only with valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 200,
        "temperature": 0.3
    }

    try:
        print("   Analyzing SQL injection attempt...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            message = data['choices'][0]['message']['content']
            print(f"   ✅ AI Response:\n{message}")

            # Try to parse JSON
            if '{' in message:
                json_start = message.index('{')
                json_end = message.rindex('}') + 1
                json_str = message[json_start:json_end]
                result = json.loads(json_str)
                print(f"\n   📊 Classification: {result['classification']}")
                print(f"   📈 Confidence: {result['confidence']}")
                print(f"   💡 Reasoning: {result['reasoning']}")
                return True
        else:
            print(f"   ❌ Error: {response.text}")
            return False

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("LiteLLM API Testing Suite")
    print("=" * 60)

    # Test 1: Basic connection
    test1_passed = test_litellm_connection()

    # Test 2: Log classification
    test2_passed = test_log_classification()

    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Connection Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"  Classification Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("=" * 60)
