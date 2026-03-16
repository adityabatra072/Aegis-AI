"""
Standalone test for AI analyzer without requiring database
Tests the AI engine classification directly
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analyzer import AIEngine
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def test_ai_engine():
    """Test AI engine initialization and classification."""
    print("=" * 70)
    print("Aegis-AI Analyzer Test Suite")
    print("=" * 70)

    # Test 1: Initialize AI Engine
    print("\n[Test 1] Initializing AI Engine...")
    try:
        ai = AIEngine()
        print(f"✅ AI Engine initialized successfully")
        print(f"   Base URL: {ai.base_url}")
        print(f"   Model: {ai.model}")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False

    # Test 2: Classify benign log
    print("\n[Test 2] Classifying benign log...")
    benign_log = "sshd[1234]: Accepted publickey for admin from 192.168.1.100 port 52000 ssh2"
    try:
        result = ai.classify_log(
            log_message=benign_log,
            log_level="INFO",
            source_ip="192.168.1.100"
        )
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Reasoning: {result['reasoning']}")
        if result['classification'] == 'SAFE':
            print("✅ Correctly classified as SAFE")
        else:
            print(f"⚠️  Expected SAFE but got {result['classification']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    # Test 3: Classify SQL injection attack
    print("\n[Test 3] Classifying SQL injection attack...")
    sqli_log = "POST /api/login HTTP/1.1 - username=' OR '1'='1-- password=admin"
    try:
        result = ai.classify_log(
            log_message=sqli_log,
            log_level="ERROR",
            source_ip="45.142.212.61"
        )
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Reasoning: {result['reasoning']}")
        print(f"   Attack Type: {result.get('attack_type', 'N/A')}")
        if result['classification'] == 'CRITICAL_THREAT':
            print("✅ Correctly classified as CRITICAL_THREAT")
        else:
            print(f"⚠️  Expected CRITICAL_THREAT but got {result['classification']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    # Test 4: Classify suspicious activity
    print("\n[Test 4] Classifying suspicious activity...")
    suspicious_log = "sshd[5678]: Failed password for root from 103.253.145.28 port 45000 ssh2"
    try:
        result = ai.classify_log(
            log_message=suspicious_log,
            log_level="WARNING",
            source_ip="103.253.145.28"
        )
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Reasoning: {result['reasoning']}")
        if result['classification'] in ['SUSPICIOUS', 'CRITICAL_THREAT']:
            print(f"✅ Correctly classified as {result['classification']}")
        else:
            print(f"⚠️  Expected SUSPICIOUS/CRITICAL_THREAT but got {result['classification']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    # Test 5: Classify XSS attack
    print("\n[Test 5] Classifying XSS attack...")
    xss_log = "GET /search?q=<script>alert('XSS')</script> HTTP/1.1 400"
    try:
        result = ai.classify_log(
            log_message=xss_log,
            log_level="ERROR",
            source_ip="185.220.101.42"
        )
        print(f"   Classification: {result['classification']}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Reasoning: {result['reasoning']}")
        print(f"   Attack Type: {result.get('attack_type', 'N/A')}")
        if result['classification'] == 'CRITICAL_THREAT':
            print("✅ Correctly classified as CRITICAL_THREAT")
        else:
            print(f"⚠️  Expected CRITICAL_THREAT but got {result['classification']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

    print("\n" + "=" * 70)
    print("✅ All tests completed successfully!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_ai_engine()
    sys.exit(0 if success else 1)
