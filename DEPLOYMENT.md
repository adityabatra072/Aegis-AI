# Aegis-AI Deployment Guide

## Quick Start with Docker

### Prerequisites
- Docker Desktop or Docker Engine installed
- Docker Compose V2 installed

### Launch the System

```bash
# Clone the repository (if not already done)
git clone https://github.com/adityabatra072/Aegis-AI.git
cd Aegis-AI

# Start all services
docker compose up -d

# Monitor logs
docker compose logs -f

# Check service status
docker compose ps
```

### Verify Deployment

```bash
# Check API health
curl http://localhost:8000/health

# View system statistics
curl http://localhost:8000/status

# Query recent threats
curl "http://localhost:8000/threats?hours=1&limit=10"
```

### Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration for Production

### Using Real AI Models

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-your-actual-openai-key-here

# OR Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# Service Configuration
LOG_GENERATION_INTERVAL=2
ANALYSIS_INTERVAL=5
```

Then restart services:
```bash
docker compose down
docker compose up -d
```

### Database Credentials

For production, update database credentials in `docker-compose.yml`:

```yaml
environment:
  POSTGRES_DB: aegis_db
  POSTGRES_USER: your_secure_username
  POSTGRES_PASSWORD: your_very_secure_password
```

**IMPORTANT**: Never commit production credentials to version control!

## Testing Without Docker

If Docker is not available, you can run services locally:

### 1. Install PostgreSQL
Install PostgreSQL 15 and create database:
```bash
createdb aegis_db
psql aegis_db < config/init.sql
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/aegis_db"
export OPENAI_API_KEY="your-key-here"  # Optional
```

### 4. Run Services
```bash
# Terminal 1: Log Generator
python src/generator.py

# Terminal 2: AI Analyzer
python src/analyzer.py

# Terminal 3: API Gateway
python src/main.py
```

## Troubleshooting

### Container Fails to Start
```bash
# View detailed logs
docker compose logs <service-name>

# Common services: postgres, generator, analyzer, api
docker compose logs postgres
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Port Already in Use
If port 8000 or 5432 is already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Change external port
```

## Monitoring in Production

### Container Health
```bash
docker compose ps
docker stats
```

### Database Size
```bash
docker compose exec postgres psql -U aegis_user -d aegis_db -c "SELECT pg_size_pretty(pg_database_size('aegis_db'));"
```

### Service Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f analyzer
```

## Stopping the System

```bash
# Stop all services (keep data)
docker compose stop

# Stop and remove containers (keep volumes)
docker compose down

# Stop and remove everything (including database)
docker compose down -v
```

## Backup Database

```bash
# Create backup
docker compose exec postgres pg_dump -U aegis_user aegis_db > backup.sql

# Restore backup
docker compose exec -T postgres psql -U aegis_user aegis_db < backup.sql
```

## Performance Tuning

### Increase Log Generation Rate
Modify `docker-compose.yml`:
```yaml
environment:
  LOG_GENERATION_INTERVAL: 1  # Generate every 1 second
```

### Increase Analysis Throughput
```yaml
environment:
  ANALYSIS_INTERVAL: 3  # Analyze every 3 seconds
```

### Scale Analyzer Service
```bash
docker compose up -d --scale analyzer=3
```

---

For support: adityabatra072@gmail.com
