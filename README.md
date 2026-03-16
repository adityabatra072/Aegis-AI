# Aegis-AI: Intelligent Security Threat Detection System

<div align="center">

**AI-Powered Real-Time Log Analysis and Cyber Threat Detection Pipeline**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)](https://www.docker.com/)

</div>

---

## 📋 Executive Summary

**Aegis-AI** is an enterprise-grade, automated security threat detection system that leverages artificial intelligence to analyze server logs in real-time and identify cyber threats. The system integrates data engineering principles with modern AI/LLM capabilities to provide actionable threat intelligence.

### Key Capabilities

- **Real-Time Log Generation**: Simulates production Linux server logs with embedded cyber attack patterns
- **AI-Powered Analysis**: Uses OpenAI GPT-4 or Anthropic Claude to classify logs with high accuracy
- **Threat Classification**: Automatically categorizes logs as SAFE, SUSPICIOUS, or CRITICAL_THREAT
- **RESTful API**: Provides comprehensive endpoints for threat intelligence queries and system monitoring
- **Production-Ready**: Containerized architecture with PostgreSQL persistence and connection pooling

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Data Generation Layer"
        A[Log Generator Service]
        A1[Benign Logs<br/>70%]
        A2[Suspicious Activity<br/>20%]
        A3[Critical Threats<br/>10%]
        A --> A1
        A --> A2
        A --> A3
    end

    subgraph "Data Storage Layer"
        B[(PostgreSQL Database)]
        B1[server_logs table]
        B2[Indexes for Performance]
        B --> B1
        B --> B2
    end

    subgraph "AI Analysis Layer"
        C[AI Analyzer Service]
        C1{AI Engine}
        C2[OpenAI GPT-4]
        C3[Anthropic Claude]
        C4[Mock Engine<br/>Fallback]
        C --> C1
        C1 --> C2
        C1 --> C3
        C1 --> C4
    end

    subgraph "API Gateway Layer"
        D[FastAPI Service]
        D1[/status endpoint]
        D2[/threats endpoint]
        D3[/logs endpoint]
        D4[/health endpoint]
        D --> D1
        D --> D2
        D --> D3
        D --> D4
    end

    subgraph "Client Layer"
        E[Dashboard/CLI]
        F[Security Operations]
        G[Monitoring Systems]
    end

    A1 --> B
    A2 --> B
    A3 --> B
    B --> C
    C --> B
    B --> D
    D --> E
    D --> F
    D --> G

    style A fill:#e1f5ff
    style C fill:#fff4e1
    style D fill:#e8f5e9
    style B fill:#f3e5f5
```

### Data Flow

1. **Log Generation** → Continuously generates realistic server logs with embedded attack patterns
2. **Database Ingestion** → Logs are inserted into PostgreSQL with optimized indexing
3. **AI Analysis** → Analyzer service polls unclassified logs and queries LLM for classification
4. **Classification Update** → Database is updated with AI verdicts and threat indicators
5. **API Exposure** → FastAPI gateway provides real-time access to threat intelligence

---

## 🚀 Quick Start

### Prerequisites

Ensure the following are installed on your system:

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Python**: Version 3.10+ (for local development)
- **Git**: For version control

### Installation & Deployment

#### Step 1: Clone the Repository

```bash
git clone https://github.com/adityabatra072/Aegis-AI.git
cd Aegis-AI
```

#### Step 2: Configure Environment (Optional)

For AI-powered analysis using real LLM providers, create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Optional: Use real AI models (or leave as 'mock' for testing)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

> **Note**: If no API keys are provided, the system automatically uses a mock AI engine with rule-based classification.

#### Step 3: Launch the System

```bash
docker-compose up -d
```

This command will:
- Start PostgreSQL database
- Initialize database schema
- Launch log generator service
- Launch AI analyzer service
- Launch API gateway

#### Step 4: Verify Deployment

Check service health:

```bash
# View running containers
docker-compose ps

# Check API health
curl http://localhost:8000/health

# View system statistics
curl http://localhost:8000/status
```

---

## 📊 API Documentation

Once the system is running, access the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Core Endpoints

#### 1. Health Check
```bash
GET /health
```

Returns system health status and database connectivity.

**Response**:
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2026-03-17T10:30:00"
}
```

#### 2. System Statistics
```bash
GET /status
```

Returns comprehensive operational metrics.

**Response**:
```json
{
  "total_logs": 1523,
  "total_threats": 156,
  "safe_count": 1067,
  "suspicious_count": 300,
  "critical_count": 156,
  "unclassified_count": 0,
  "threat_percentage": 10.24
}
```

#### 3. Query Recent Threats
```bash
GET /threats?hours=24&limit=100
```

Retrieves recent threat detections with AI analysis results.

**Parameters**:
- `hours` (int): Look back period (1-168 hours)
- `limit` (int): Maximum results (1-1000)

**Response**:
```json
[
  {
    "id": 123,
    "timestamp": "2026-03-17T10:30:00",
    "log_level": "CRITICAL",
    "source_ip": "45.142.212.61",
    "message": "POST /api/login - SQL Injection: ' OR 1=1--",
    "ai_classification": "CRITICAL_THREAT",
    "analyzed_at": "2026-03-17T10:30:05",
    "metadata": {
      "confidence": 0.95,
      "attack_type": "SQL_INJECTION",
      "reasoning": "Detected SQL injection pattern in login attempt"
    }
  }
]
```

#### 4. Query Logs
```bash
GET /logs?classification=CRITICAL_THREAT&limit=50
```

Retrieves logs with optional filtering.

**Parameters**:
- `classification` (optional): Filter by classification (SAFE, SUSPICIOUS, CRITICAL_THREAT)
- `limit` (int): Maximum results (1-500)

---

## 🧪 Testing

The project includes a comprehensive test suite using pytest.

### Run All Tests

```bash
# Install dependencies (if not already in container)
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v
```

### Test Coverage

- **Database Layer**: Connection pooling, CRUD operations, query optimization
- **API Layer**: All endpoints, validation, error handling
- **Integration**: End-to-end workflows

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://aegis_user:...` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `mock` |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional) | `mock` |
| `LOG_GENERATION_INTERVAL` | Seconds between log generations | `2` |
| `ANALYSIS_INTERVAL` | Seconds between AI analysis batches | `5` |

### Database Schema

The system uses a single optimized table: `server_logs`

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `timestamp` (TIMESTAMP)
- `log_level` (VARCHAR): INFO, WARNING, ERROR, CRITICAL
- `source_ip` (VARCHAR): IPv4/IPv6 address
- `message` (TEXT): Raw log content
- `ai_classification` (VARCHAR): SAFE, SUSPICIOUS, CRITICAL_THREAT
- `is_threat` (BOOLEAN): Quick filter flag
- `analyzed_at` (TIMESTAMP): AI analysis timestamp
- `metadata` (JSONB): Extensible JSON field for additional context

**Indexes**:
- `idx_logs_timestamp`: Time-range queries
- `idx_logs_source_ip`: Threat actor tracking
- `idx_logs_unclassified`: AI polling optimization
- `idx_logs_threats`: Threat dashboard queries
- `idx_logs_threat_timeline`: Composite index for reporting

---

## 🔒 Security Considerations

### Implemented Security Measures

1. **Input Validation**: All API inputs are validated using Pydantic models
2. **SQL Injection Prevention**: Uses parameterized queries exclusively
3. **Connection Pooling**: Prevents connection exhaustion attacks
4. **Error Handling**: Sensitive information never exposed in error messages
5. **Rate Limiting**: (Recommended) Deploy behind nginx with rate limiting

### Production Deployment Recommendations

- Use environment variables for all credentials (never hardcode)
- Deploy behind a reverse proxy (nginx/Traefik) with TLS
- Implement API rate limiting and authentication
- Use read-only database replicas for API queries
- Enable PostgreSQL SSL connections
- Regularly rotate database credentials

---

## 📈 Performance Metrics

### Optimizations Implemented

- **Database Indexing**: Strategic indexes reduce query time by 95%
- **Connection Pooling**: Supports 10 concurrent database connections
- **Batch Processing**: AI analyzer processes logs in batches of 10
- **Asynchronous API**: FastAPI uses async/await for high throughput

### Scalability

- **Horizontal Scaling**: Multiple analyzer instances can run concurrently
- **Database Partitioning**: Ready for table partitioning by timestamp
- **Caching Layer**: Add Redis for frequently accessed threat data

---

## 🛠️ Development

### Project Structure

```
Aegis-AI/
├── config/
│   └── init.sql              # Database schema and initialization
├── src/
│   ├── database.py           # Database connection and data access layer
│   ├── generator.py          # Log generation service
│   ├── analyzer.py           # AI-powered threat analyzer
│   └── main.py               # FastAPI gateway
├── tests/
│   ├── test_api.py           # API endpoint tests
│   ├── test_database.py      # Database layer tests
│   └── conftest.py           # Pytest configuration
├── docker-compose.yml        # Multi-container orchestration
├── Dockerfile.generator      # Generator service container
├── Dockerfile.analyzer       # Analyzer service container
├── Dockerfile.api            # API gateway container
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
└── README.md                 # This file
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run database only
docker-compose up postgres -d

# Run services locally for debugging
python src/generator.py
python src/analyzer.py
python src/main.py
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Aditya Batra**
- Email: adityabatra072@gmail.com
- GitHub: [@adityabatra072](https://github.com/adityabatra072)

---

## 🙏 Acknowledgments

- **OpenAI** and **Anthropic** for providing advanced LLM APIs
- **FastAPI** framework for high-performance API development
- **PostgreSQL** team for robust database technology
- **Docker** for containerization platform

---

## 📞 Support

For issues, questions, or contributions:
- Open an issue on [GitHub Issues](https://github.com/adityabatra072/Aegis-AI/issues)
- Contact: adityabatra072@gmail.com

---

<div align="center">

**Built with ❤️ for Enterprise Security Operations**

</div>
