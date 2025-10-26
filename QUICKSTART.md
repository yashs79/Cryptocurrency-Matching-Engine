# Quick Start Guide - Cryptocurrency Matching Engine

Get up and running in 5 minutes! 🚀

---

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

---

## 🚀 Quick Setup (5 minutes)

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone and enter directory
cd "/Users/yash/goquant task"

# 2. Run setup script
./scripts/setup.sh

# 3. Start all services
make docker-up

# 4. Verify deployment
./scripts/test-deployment.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create environment file
cp .env.example .env

# 4. Start services with Docker
docker-compose up -d

# 5. Run tests
pytest tests/ -v
```

---

## ✅ Verify Installation

### Check Services

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"matching-engine","version":"1.0.0"}

# API documentation
open http://localhost:8000/docs

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Check All Endpoints

| Service | URL | Status |
|---------|-----|--------|
| API | http://localhost:8000 | ✅ |
| API Docs | http://localhost:8000/docs | ✅ |
| Metrics | http://localhost:8000/metrics | ✅ |
| Prometheus | http://localhost:9091 | ✅ |
| Grafana | http://localhost:3000 | ✅ |
| PostgreSQL | localhost:5432 | ✅ |
| Redis | localhost:6379 | ✅ |

---

## 🧪 Run Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# With coverage report
make test-cov

# View coverage report
open htmlcov/index.html
```

---

## 🛠️ Development Workflow

### Start Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server with auto-reload
make dev

# Or manually:
uvicorn src.matching_engine.main:app --reload --host 0.0.0.0 --port 8000
```

### Make Code Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes to code

# 3. Format code
make format

# 4. Run linters
make lint

# 5. Run tests
make test

# 6. Commit and push
git add .
git commit -m "feat: add my feature"
git push origin feature/my-feature
```

### CI/CD Pipeline

When you push code, GitHub Actions automatically:
1. ✅ Runs code quality checks
2. ✅ Runs all tests
3. ✅ Scans for security issues
4. ✅ Builds Docker image
5. ✅ Runs integration tests
6. ✅ Deploys to dev (if on develop branch)

---

## 📊 View Monitoring

### Prometheus

```bash
# Open Prometheus UI
open http://localhost:9091

# Query examples:
# - up{job="matching-engine"}
# - process_cpu_seconds_total
# - process_resident_memory_bytes
```

### Grafana

```bash
# Open Grafana
open http://localhost:3000

# Login:
# Username: admin
# Password: admin

# Dashboards will be added in Phase 7
```

---

## 🐳 Docker Commands

```bash
# Start all services
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs

# Rebuild image
make docker-build

# Restart services
make docker-down && make docker-up
```

---

## 📖 API Examples

### Health Check

```bash
curl http://localhost:8000/health
```

### Root Endpoint

```bash
curl http://localhost:8000/
```

### Interactive API Docs

Open http://localhost:8000/docs in your browser to:
- View all endpoints
- Test API calls interactively
- See request/response schemas

---

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

### Docker Issues

```bash
# Clean up everything
make docker-down
make clean
docker system prune -a

# Rebuild from scratch
make docker-build
make docker-up
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs matching-postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Tests Failing

```bash
# Clean and reinstall
make clean
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run tests
make test
```

---

## 📚 Next Steps

### For Development

1. **Read the Development Plan**
   ```bash
   cat DEVELOPMENT_PLAN.md
   ```

2. **Check Project Status**
   ```bash
   cat PROJECT_STATUS.md
   ```

3. **Review Architecture**
   ```bash
   cat docs/architecture_design.md
   ```

4. **Start Building Phase 1**
   - Create data models
   - Implement order book
   - Build matching engine

### For Deployment

1. **Configure Environment**
   - Update `.env` with production values
   - Set up secrets in GitHub

2. **Set Up Kubernetes** (Optional)
   - Review `infrastructure/kubernetes/`
   - Configure kubectl
   - Deploy with Helm

3. **Configure Monitoring**
   - Set up alerts in Prometheus
   - Create Grafana dashboards
   - Configure log aggregation

---

## 🎯 Current Status

✅ **Phase 0 Complete**: CI/CD Pipeline Setup

**What's Working:**
- FastAPI application with health checks
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Monitoring infrastructure (Prometheus/Grafana)
- Testing framework
- Development environment

**What's Next:**
- Phase 1: Core Engine Foundation
- Implement order book
- Build matching algorithm

---

## 💡 Useful Commands

```bash
# Development
make dev              # Start dev server
make test             # Run tests
make lint             # Check code quality
make format           # Format code

# Docker
make docker-up        # Start services
make docker-down      # Stop services
make docker-logs      # View logs

# Testing
make test-unit        # Unit tests
make test-integration # Integration tests
make test-cov         # Coverage report

# Cleanup
make clean            # Clean temp files
```

---

## 📞 Getting Help

- **Documentation**: Check `/docs` directory
- **Development Plan**: `DEVELOPMENT_PLAN.md`
- **Project Status**: `PROJECT_STATUS.md`
- **Architecture**: `docs/architecture_design.md`
- **API Docs**: http://localhost:8000/docs

---

## 🎉 You're Ready!

Your development environment is set up and ready to go!

**Next Steps:**
1. Explore the API at http://localhost:8000/docs
2. Review DEVELOPMENT_PLAN.md for implementation details
3. Start building Phase 1 features
4. Test each feature in the deployed environment

Happy coding! 🚀
