CI/CD Pipeline Plan for Matching Engine
Deployment-First Development Strategy

Executive Summary
This comprehensive CI/CD pipeline implements a deployment-first approach, enabling you to test every feature in a production-like environment from day one. The pipeline covers everything from code commit to production deployment with automated testing, security scanning, and rollback capabilities.

1. CI/CD Architecture Overview
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER WORKFLOW                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │   Git Push/PR        │
                    │   (GitHub/GitLab)    │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌────────────────┐     ┌───────────────┐
│  CODE QUALITY │      │  UNIT TESTS    │     │  SECURITY     │
│  - Lint       │      │  - pytest      │     │  - Bandit     │
│  - Format     │      │  - Coverage    │     │  - Safety     │
│  - Type Check │      │  - Benchmark   │     │  - Trivy      │
└───────┬───────┘      └────────┬───────┘     └───────┬───────┘
        │                       │                      │
        └───────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  BUILD DOCKER IMAGE  │
                    │  - Multi-stage       │
                    │  - Tag & Push        │
                    └───────────┬──────────┘
                                │
                    ┌───────────▼──────────┐
                    │  INTEGRATION TESTS   │
                    │  - API Tests         │
                    │  - E2E Tests         │
                    └───────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌────────────────┐     ┌───────────────┐
│  DEV ENV      │      │  STAGING ENV   │     │  PROD ENV     │
│  - Auto       │      │  - Manual      │     │  - Manual     │
│  - Feature    │      │  - Pre-prod    │     │  - Blue/Green │
│  Testing      │      │  - Full Test   │     │  - Canary     │
└───────────────┘      └────────────────┘     └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │  MONITORING          │
                    │  - Prometheus        │
                    │  - Grafana           │
                    │  - Alerts            │
                    └──────────────────────┘

2. Technology Stack for CI/CD
2.1 Core Tools
yamlVersion Control:
  - GitHub (recommended) or GitLab
  - Branch Protection Rules
  - PR/MR Templates

CI/CD Platform:
  Primary: GitHub Actions (or GitLab CI)
  Alternative: Jenkins, CircleCI, Travis CI

Container Registry:
  - Docker Hub
  - GitHub Container Registry (GHCR)
  - AWS ECR
  - Google Container Registry (GCR)

Infrastructure:
  - Kubernetes (K8s) - Production
  - Docker Compose - Development/Staging
  - Terraform/Pulumi - IaC
  - Helm - K8s Package Manager

Monitoring & Observability:
  - Prometheus - Metrics
  - Grafana - Dashboards
  - ELK/Loki - Logs
  - Jaeger - Tracing
  - Sentry - Error Tracking

Testing:
  - pytest - Unit/Integration
  - Locust - Load Testing
  - k6 - Performance Testing
  - Postman/Newman - API Testing

Security:
  - Trivy - Container Scanning
  - Bandit - Python Security
  - Safety - Dependency Check
  - OWASP ZAP - Security Testing
  - SonarQube - Code Quality
```

---

## 3. Repository Structure
```
matching-engine/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Main CI pipeline
│   │   ├── cd-dev.yml                # Deploy to Dev
│   │   ├── cd-staging.yml            # Deploy to Staging
│   │   ├── cd-production.yml         # Deploy to Production
│   │   ├── security-scan.yml         # Security scanning
│   │   ├── performance-test.yml      # Performance tests
│   │   └── cleanup.yml               # Cleanup old resources
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── .gitlab-ci.yml                    # GitLab CI (alternative)
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── configmap.yaml
│   │   │   └── secrets.yaml
│   │   ├── overlays/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── production/
│   │   └── helm/
│   │       └── matching-engine/
│   │           ├── Chart.yaml
│   │           ├── values.yaml
│   │           ├── values-dev.yaml
│   │           ├── values-staging.yaml
│   │           └── values-production.yaml
│   └── docker/
│       ├── Dockerfile
│       ├── Dockerfile.dev
│       └── docker-compose.yml
├── scripts/
│   ├── ci/
│   │   ├── run-tests.sh
│   │   ├── build-image.sh
│   │   ├── security-scan.sh
│   │   └── deploy.sh
│   ├── local-dev/
│   │   ├── setup.sh
│   │   └── cleanup.sh
│   └── monitoring/
│       ├── setup-prometheus.sh
│       └── setup-grafana.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── performance/
│   └── security/
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── loki/
│       └── loki-config.yml
├── docs/
│   ├── DEPLOYMENT.md
│   ├── RUNBOOK.md
│   └── ARCHITECTURE.md
├── src/
├── config/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── setup.py
├── pyproject.toml
├── .dockerignore
├── .gitignore
└── README.md

4. GitHub Actions CI/CD Pipeline
4.1 Main CI Pipeline (.github/workflows/ci.yml)
yamlname: CI Pipeline

on:
  push:
    branches: [main, develop, 'feature/**']
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: '3.11'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================
  # JOB 1: Code Quality Checks
  # ============================================
  code-quality:
    name: Code Quality
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install black flake8 isort mypy bandit safety
          pip install -r requirements.txt
      
      - name: Run Black (Format Check)
        run: black --check src/ tests/
      
      - name: Run isort (Import Order Check)
        run: isort --check-only src/ tests/
      
      - name: Run Flake8 (Linting)
        run: flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203
      
      - name: Run MyPy (Type Checking)
        run: mypy src/ --ignore-missing-imports
      
      - name: Run Bandit (Security Linting)
        run: bandit -r src/ -f json -o bandit-report.json
        continue-on-error: true
      
      - name: Upload Bandit Report
        uses: actions/upload-artifact@v4
        with:
          name: bandit-report
          path: bandit-report.json

  # ============================================
  # JOB 2: Unit Tests
  # ============================================
  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: code-quality
    
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio pytest-benchmark
      
      - name: Run Unit Tests
        run: |
          pytest tests/unit/ \
            -v \
            --cov=src/matching_engine \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term \
            --junit-xml=pytest-report.xml
      
      - name: Upload Coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      
      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: pytest-results-${{ matrix.python-version }}
          path: |
            pytest-report.xml
            htmlcov/

  # ============================================
  # JOB 3: Security Scanning
  # ============================================
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: code-quality
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install safety pip-audit
          pip install -r requirements.txt
      
      - name: Run Safety Check (Known Vulnerabilities)
        run: safety check --json --output safety-report.json
        continue-on-error: true
      
      - name: Run pip-audit (Dependency Audit)
        run: pip-audit --desc --output pip-audit-report.json
        continue-on-error: true
      
      - name: Upload Security Reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            safety-report.json
            pip-audit-report.json

  # ============================================
  # JOB 4: Build Docker Image
  # ============================================
  build-image:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [unit-tests, security-scan]
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract Metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      - name: Build and Push Docker Image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_DATE=${{ github.event.head_commit.timestamp }}
            VCS_REF=${{ github.sha }}
            VERSION=${{ github.ref_name }}
      
      - name: Generate SBOM (Software Bill of Materials)
        uses: anchore/sbom-action@v0
        with:
          image: ${{ steps.meta.outputs.tags }}
          format: spdx-json
          output-file: sbom.spdx.json
      
      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.spdx.json

  # ============================================
  # JOB 5: Container Security Scan
  # ============================================
  container-scan:
    name: Container Security Scan
    runs-on: ubuntu-latest
    needs: build-image
    
    steps:
      - name: Run Trivy Vulnerability Scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ needs.build-image.outputs.image-tag }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload Trivy Results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Run Trivy (JSON Report)
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ needs.build-image.outputs.image-tag }}
          format: 'json'
          output: 'trivy-results.json'
      
      - name: Upload Trivy JSON Report
        uses: actions/upload-artifact@v4
        with:
          name: trivy-report
          path: trivy-results.json

  # ============================================
  # JOB 6: Integration Tests
  # ============================================
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: build-image
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: matching_engine_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Pull Docker Image
        run: docker pull ${{ needs.build-image.outputs.image-tag }}
      
      - name: Start Services with Docker Compose
        run: |
          cat > docker-compose.test.yml <<EOF
          version: '3.8'
          services:
            matching-engine:
              image: ${{ needs.build-image.outputs.image-tag }}
              ports:
                - "8000:8000"
                - "8765:8765"
                - "9090:9090"
              environment:
                - DATABASE_URL=postgresql://postgres:testpass@postgres:5432/matching_engine_test
              depends_on:
                - postgres
            postgres:
              image: postgres:15-alpine
              environment:
                POSTGRES_PASSWORD: testpass
                POSTGRES_DB: matching_engine_test
          EOF
          docker-compose -f docker-compose.test.yml up -d
          sleep 10
      
      - name: Wait for Services to be Healthy
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
      
      - name: Run Integration Tests
        run: |
          pytest tests/integration/ -v --junit-xml=integration-report.xml
        env:
          API_BASE_URL: http://localhost:8000
          WS_URL: ws://localhost:8765
      
      - name: Show Container Logs
        if: failure()
        run: docker-compose -f docker-compose.test.yml logs
      
      - name: Cleanup
        if: always()
        run: docker-compose -f docker-compose.test.yml down -v
      
      - name: Upload Integration Test Results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: integration-test-results
          path: integration-report.xml

  # ============================================
  # JOB 7: Performance Tests
  # ============================================
  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    needs: build-image
    if: github.event_name == 'pull_request' || github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Pull Docker Image
        run: docker pull ${{ needs.build-image.outputs.image-tag }}
      
      - name: Start Matching Engine
        run: |
          docker run -d \
            --name matching-engine \
            -p 8000:8000 \
            ${{ needs.build-image.outputs.image-tag }}
          sleep 10
      
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      
      - name: Run k6 Load Test
        run: |
          cat > load-test.js <<'EOF'
          import http from 'k6/http';
          import { check, sleep } from 'k6';

          export const options = {
            stages: [
              { duration: '30s', target: 50 },
              { duration: '1m', target: 100 },
              { duration: '30s', target: 0 },
            ],
            thresholds: {
              http_req_duration: ['p(95)<500'],
              http_req_failed: ['rate<0.01'],
            },
          };

          export default function () {
            const payload = JSON.stringify({
              symbol: 'BTC-USDT',
              order_type: 'limit',
              side: 'buy',
              quantity: '0.1',
              price: '45000.00'
            });

            const params = {
              headers: {
                'Content-Type': 'application/json',
              },
            };

            const res = http.post('http://localhost:8000/api/v1/orders', payload, params);
            
            check(res, {
              'status is 200': (r) => r.status === 200 || r.status === 201,
              'response time < 500ms': (r) => r.timings.duration < 500,
            });

            sleep(1);
          }
          EOF
          k6 run --out json=load-test-results.json load-test.js
      
      - name: Upload Performance Results
        uses: actions/upload-artifact@v4
        with:
          name: performance-results
          path: load-test-results.json
      
      - name: Cleanup
        if: always()
        run: docker rm -f matching-engine

  # ============================================
  # JOB 8: Notify on Failure
  # ============================================
  notify-failure:
    name: Notify on Failure
    runs-on: ubuntu-latest
    needs: [code-quality, unit-tests, security-scan, build-image, integration-tests]
    if: failure()
    
    steps:
      - name: Send Slack Notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'CI Pipeline Failed!'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
4.2 Deploy to Development (.github/workflows/cd-dev.yml)
yamlname: Deploy to Development

on:
  push:
    branches: [develop, 'feature/**']
  workflow_dispatch:

env:
  ENVIRONMENT: dev
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  KUBE_NAMESPACE: matching-engine-dev

jobs:
  deploy-dev:
    name: Deploy to Dev Environment
    runs-on: ubuntu-latest
    environment:
      name: development
      url: https://dev.matching-engine.example.com
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
        with:
          version: 'latest'
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_DEV }}" | base64 -d > kubeconfig
          export KUBECONFIG=./kubeconfig
      
      - name: Set Image Tag
        id: image
        run: |
          IMAGE_TAG="${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.ref_name }}-${{ github.sha }}"
          echo "tag=$IMAGE_TAG" >> $GITHUB_OUTPUT
      
      - name: Deploy with Helm
        run: |
          helm upgrade --install matching-engine \
            ./infrastructure/kubernetes/helm/matching-engine \
            --namespace ${{ env.KUBE_NAMESPACE }} \
            --create-namespace \
            --values ./infrastructure/kubernetes/helm/matching-engine/values-dev.yaml \
            --set image.tag=${{ steps.image.outputs.tag }} \
            --set image.pullPolicy=Always \
            --wait \
            --timeout 5m
      
      - name: Verify Deployment
        run: |
          kubectl rollout status deployment/matching-engine \
            -n ${{ env.KUBE_NAMESPACE }} \
            --timeout=5m
      
      - name: Run Smoke Tests
        run: |
          DEV_URL="https://dev.matching-engine.example.com"
          
          # Health check
          curl -f $DEV_URL/health || exit 1
          
          # API test
          curl -f -X POST $DEV_URL/api/v1/orders \
            -H "Content-Type: application/json" \
            -d '{"symbol":"BTC-USDT","order_type":"limit","side":"buy","quantity":"0.1","price":"45000"}' \
            || exit 1
      
      - name: Post Deployment Info
        run: |
          echo "🚀 Deployed to Development"
          echo "URL: https://dev.matching-engine.example.com"
          echo "Image: ${{ steps.image.outputs.tag }}"
          echo "Namespace: ${{ env.KUBE_NAMESPACE }}"
      
      - name: Notify Slack
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployed to Development Environment'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        if: always()
4.3 Deploy to Staging (.github/workflows/cd-staging.yml)
yamlname: Deploy to Staging

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  ENVIRONMENT: staging
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  KUBE_NAMESPACE: matching-engine-staging

jobs:
  deploy-staging:
    name: Deploy to Staging Environment
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.matching-engine.example.com
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=./kubeconfig
      
      - name: Set Image Tag
        id: image
        run: |
          IMAGE_TAG="${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest"
          echo "tag=$IMAGE_TAG" >> $GITHUB_OUTPUT
      
      - name: Deploy with Helm
        run: |
          helm upgrade --install matching-engine \
            ./infrastructure/kubernetes/helm/matching-engine \
            --namespace ${{ env.KUBE_NAMESPACE }} \
            --create-namespace \
            --values ./infrastructure/kubernetes/helm/matching-engine/values-staging.yaml \
            --set image.tag=${{ steps.image.outputs.tag }} \
            --wait \
            --timeout 10m
      
      - name: Verify Deployment
        run: |
          kubectl rollout status deployment/matching-engine \
            -n ${{ env.KUBE_NAMESPACE }} \
            --timeout=10m
      
      - name: Run E2E Tests
        run: |
          pip install pytest requests websockets
          pytest tests/e2e/ \
            --base-url=https://staging.matching-engine.example.com \
            -v
      
      - name: Run Load Tests
        run: |
          # Run load test against staging
          k6 run --vus 50 --duration 5m tests/performance/load-test.js
      
      - name: Notify on Success
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: '✅ Deployed to Staging - Ready for Production'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
4.4 Deploy to Production (.github/workflows/cd-production.yml)
yamlname: Deploy to Production

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true

env:
  ENVIRONMENT: production
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  KUBE_NAMESPACE: matching-engine-prod

jobs:
  pre-deployment-checks:
    name: Pre-Deployment Checks
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Verify Release Tag
        run: |
          if [[ ! "${{ github.ref }}" =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "Invalid release tag format"
            exit 1
          fi
      
      - name: Check Staging Health
        run: |
          curl -f https://staging.matching-engine.example.com/health || exit 1
      
      - name: Verify All Tests Passed
        run: |
          echo "Checking test results from staging..."
          # Add logic to verify staging tests passed

  deploy-production:
    name: Deploy to Production (Blue-Green)
    runs-on: ubuntu-latest
    needs: pre-deployment-checks
    environment:
      name: production
      url: https://matching-engine.example.com
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Set up kubectl
        uses: azure/setup-kubectl@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_PROD }}" | base64 -d > kubeconfig
          export KUBECONFIG=./kubeconfig
      
      - name: Determine Active/Inactive Slots
        id: slots
        run: |
          ACTIVE=$(kubectl get service matching-engine-prod \
            -n ${{ env.KUBE_NAMESPACE }} \
            -o jsonpath='{.spec.selector.slot}')
          
          if [ "$ACTIVE" == "blue" ]; then
            INACTIVE="green"
          else
            INACTIVE="blue"
          fi
          
          echo "active=$ACTIVE" >> $GITHUB_OUTPUT
          echo "inactive=$INACTIVE" >> $GITHUB_OUTPUT
      
      - name: Deploy to Inactive Slot (${{ steps.slots.outputs.inactive }})
        run: |
          helm upgrade --install matching-engine-${{ steps.slots.outputs.inactive }} \
            ./infrastructure/kubernetes/helm/matching-engine \
            --namespace ${{ env.KUBE_NAMESPACE }} \
            --values ./infrastructure/kubernetes/helm/matching-engine/values-production.yaml \
            --set image.tag=${{ github.ref_name }} \
            --set slot=${{ steps.slots.outputs.inactive }} \
            --wait \
            --timeout 15m
      
      - name: Verify Inactive Slot Health
        run: |
          kubectl rollout status deployment/matching-engine-${{ steps.slots.outputs.inactive }} \
            -n ${{ env.KUBE_NAMESPACE }} \2 / 2RetryClaude does not have the ability to run the code it generates yet.YContinueyaml            --timeout=15m
          
          # Wait for pods to be ready
          kubectl wait --for=condition=ready pod \
            -l app=matching-engine,slot=${{ steps.slots.outputs.inactive }} \
            -n ${{ env.KUBE_NAMESPACE }} \
            --timeout=5m
      
      - name: Run Smoke Tests on Inactive Slot
        run: |
          # Get internal service URL for inactive slot
          INACTIVE_URL="http://matching-engine-${{ steps.slots.outputs.inactive }}.${{ env.KUBE_NAMESPACE }}.svc.cluster.local:8000"
          
          # Run smoke tests
          kubectl run smoke-test --rm -i --restart=Never \
            --image=curlimages/curl:latest \
            -n ${{ env.KUBE_NAMESPACE }} \
            -- curl -f $INACTIVE_URL/health
      
      - name: Run Canary Analysis
        id: canary
        run: |
          # Gradually shift traffic to new version
          echo "Starting canary deployment..."
          
          # 10% traffic
          kubectl patch service matching-engine-prod \
            -n ${{ env.KUBE_NAMESPACE }} \
            --type merge \
            -p '{"spec":{"selector":{"slot":"${{ steps.slots.outputs.inactive }}","weight":"10"}}}'
          
          sleep 120
          
          # Check error rate
          ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
            --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
            jq -r '.data.result[0].value[1]')
          
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate too high: $ERROR_RATE"
            echo "rollback=true" >> $GITHUB_OUTPUT
            exit 1
          fi
          
          # 50% traffic
          kubectl patch service matching-engine-prod \
            -n ${{ env.KUBE_NAMESPACE }} \
            --type merge \
            -p '{"spec":{"selector":{"slot":"${{ steps.slots.outputs.inactive }}","weight":"50"}}}'
          
          sleep 300
          
          # Final check
          ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
            --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
            jq -r '.data.result[0].value[1]')
          
          if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
            echo "Error rate too high during canary: $ERROR_RATE"
            echo "rollback=true" >> $GITHUB_OUTPUT
            exit 1
          fi
          
          echo "rollback=false" >> $GITHUB_OUTPUT
      
      - name: Switch Traffic to New Version
        if: steps.canary.outputs.rollback != 'true'
        run: |
          # Switch all traffic to inactive slot (making it active)
          kubectl patch service matching-engine-prod \
            -n ${{ env.KUBE_NAMESPACE }} \
            --type merge \
            -p '{"spec":{"selector":{"slot":"${{ steps.slots.outputs.inactive }}"}}}'
          
          echo "✅ Traffic switched to ${{ steps.slots.outputs.inactive }} slot"
      
      - name: Rollback on Failure
        if: failure() || steps.canary.outputs.rollback == 'true'
        run: |
          echo "🔄 Rolling back to ${{ steps.slots.outputs.active }} slot"
          
          kubectl patch service matching-engine-prod \
            -n ${{ env.KUBE_NAMESPACE }} \
            --type merge \
            -p '{"spec":{"selector":{"slot":"${{ steps.slots.outputs.active }}"}}}'
          
          # Delete failed deployment
          helm delete matching-engine-${{ steps.slots.outputs.inactive }} \
            -n ${{ env.KUBE_NAMESPACE }}
      
      - name: Cleanup Old Version
        if: success()
        run: |
          # Keep old version for quick rollback (delete after 24h)
          echo "Keeping old version for 24h for potential rollback"
          # helm delete matching-engine-${{ steps.slots.outputs.active }} -n ${{ env.KUBE_NAMESPACE }}
      
      - name: Create Deployment Record
        if: success()
        run: |
          cat > deployment-record.json <<EOF
          {
            "version": "${{ github.ref_name }}",
            "deployed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
            "deployed_by": "${{ github.actor }}",
            "environment": "production",
            "slot": "${{ steps.slots.outputs.inactive }}",
            "commit_sha": "${{ github.sha }}"
          }
          EOF
          
          # Store in your deployment tracking system
          # e.g., S3, database, etc.
      
      - name: Notify Success
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: success
          text: |
            🚀 Production Deployment Successful!
            Version: ${{ github.ref_name }}
            Slot: ${{ steps.slots.outputs.inactive }}
            URL: https://matching-engine.example.com
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
      
      - name: Notify Failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: failure
          text: |
            ❌ Production Deployment Failed!
            Version: ${{ github.ref_name }}
            Rolled back to: ${{ steps.slots.outputs.active }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}

  post-deployment-validation:
    name: Post-Deployment Validation
    runs-on: ubuntu-latest
    needs: deploy-production
    
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Run Production Health Checks
        run: |
          PROD_URL="https://matching-engine.example.com"
          
          # Health check
          curl -f $PROD_URL/health || exit 1
          
          # Metrics check
          curl -f $PROD_URL/metrics || exit 1
      
      - name: Run Production E2E Tests
        run: |
          pip install pytest requests websockets
          pytest tests/e2e/production-safe/ \
            --base-url=https://matching-engine.example.com \
            -v
      
      - name: Monitor for 15 Minutes
        run: |
          echo "Monitoring production metrics for 15 minutes..."
          for i in {1..15}; do
            sleep 60
            ERROR_RATE=$(curl -s http://prometheus:9090/api/v1/query \
              --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
              jq -r '.data.result[0].value[1]')
            
            echo "Minute $i: Error rate = $ERROR_RATE"
            
            if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
              echo "⚠️ High error rate detected!"
              exit 1
            fi
          done
          
          echo "✅ Production monitoring passed"

5. GitLab CI/CD Pipeline (Alternative)
5.1 .gitlab-ci.yml
yaml# GitLab CI/CD Pipeline for Matching Engine

stages:
  - quality
  - test
  - security
  - build
  - deploy-dev
  - deploy-staging
  - deploy-production

variables:
  PYTHON_VERSION: "3.11"
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_NAME: $CI_REGISTRY_IMAGE
  KUBE_NAMESPACE_DEV: matching-engine-dev
  KUBE_NAMESPACE_STAGING: matching-engine-staging
  KUBE_NAMESPACE_PROD: matching-engine-prod

# ============================================
# Quality Stage
# ============================================

code-quality:
  stage: quality
  image: python:$PYTHON_VERSION
  before_script:
    - pip install black flake8 isort mypy bandit
    - pip install -r requirements.txt
  script:
    - black --check src/ tests/
    - isort --check-only src/ tests/
    - flake8 src/ tests/ --max-line-length=88
    - mypy src/ --ignore-missing-imports
    - bandit -r src/ -f json -o bandit-report.json
  artifacts:
    reports:
      codequality: bandit-report.json
    paths:
      - bandit-report.json
    expire_in: 1 week
  only:
    - branches
    - merge_requests

# ============================================
# Test Stage
# ============================================

unit-tests:
  stage: test
  image: python:$PYTHON_VERSION
  services:
    - postgres:15-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_pass
    DATABASE_URL: postgresql://test_user:test_pass@postgres:5432/test_db
  before_script:
    - pip install -r requirements.txt
    - pip install pytest pytest-cov pytest-asyncio
  script:
    - pytest tests/unit/ 
        -v 
        --cov=src/matching_engine 
        --cov-report=xml 
        --cov-report=html
        --junit-xml=report.xml
  coverage: '/(?i)total.*? (100(?:\.0+)?\%|[1-9]?\d(?:\.\d+)?\%)$/'
  artifacts:
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    paths:
      - htmlcov/
    expire_in: 1 week
  only:
    - branches
    - merge_requests

# ============================================
# Security Stage
# ============================================

security-scan:
  stage: security
  image: python:$PYTHON_VERSION
  before_script:
    - pip install safety pip-audit
  script:
    - safety check --json --output safety-report.json || true
    - pip-audit --desc --output pip-audit.json || true
  artifacts:
    paths:
      - safety-report.json
      - pip-audit.json
    expire_in: 1 week
  only:
    - branches
    - merge_requests

# ============================================
# Build Stage
# ============================================

build-image:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      docker build \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VCS_REF=$CI_COMMIT_SHA \
        --build-arg VERSION=$CI_COMMIT_REF_NAME \
        -t $IMAGE_NAME:$CI_COMMIT_SHA \
        -t $IMAGE_NAME:$CI_COMMIT_REF_NAME \
        .
    - docker push $IMAGE_NAME:$CI_COMMIT_SHA
    - docker push $IMAGE_NAME:$CI_COMMIT_REF_NAME
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $IMAGE_NAME:$CI_COMMIT_SHA $IMAGE_NAME:latest
        docker push $IMAGE_NAME:latest
      fi
  only:
    - branches
    - tags

container-scan:
  stage: build
  image: aquasec/trivy:latest
  dependencies:
    - build-image
  script:
    - trivy image --exit-code 0 --severity HIGH,CRITICAL --format json --output trivy-report.json $IMAGE_NAME:$CI_COMMIT_SHA
  artifacts:
    paths:
      - trivy-report.json
    expire_in: 1 week
  only:
    - branches
    - merge_requests

integration-tests:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  dependencies:
    - build-image
  before_script:
    - apk add --no-cache python3 py3-pip curl
    - pip3 install pytest requests websockets
  script:
    - docker-compose -f docker-compose.test.yml up -d
    - sleep 15
    - curl -f http://localhost:8000/health
    - pytest tests/integration/ -v
  after_script:
    - docker-compose -f docker-compose.test.yml logs
    - docker-compose -f docker-compose.test.yml down -v
  only:
    - branches
    - merge_requests

# ============================================
# Deploy to Development
# ============================================

deploy-dev:
  stage: deploy-dev
  image: alpine/k8s:1.28.3
  environment:
    name: development
    url: https://dev.matching-engine.example.com
  before_script:
    - echo "$KUBECONFIG_DEV" | base64 -d > kubeconfig
    - export KUBECONFIG=./kubeconfig
  script:
    - |
      helm upgrade --install matching-engine \
        ./infrastructure/kubernetes/helm/matching-engine \
        --namespace $KUBE_NAMESPACE_DEV \
        --create-namespace \
        --values ./infrastructure/kubernetes/helm/matching-engine/values-dev.yaml \
        --set image.tag=$CI_COMMIT_SHA \
        --wait \
        --timeout 5m
    - kubectl rollout status deployment/matching-engine -n $KUBE_NAMESPACE_DEV
  only:
    - develop
    - /^feature\/.*/

# ============================================
# Deploy to Staging
# ============================================

deploy-staging:
  stage: deploy-staging
  image: alpine/k8s:1.28.3
  environment:
    name: staging
    url: https://staging.matching-engine.example.com
  before_script:
    - echo "$KUBECONFIG_STAGING" | base64 -d > kubeconfig
    - export KUBECONFIG=./kubeconfig
  script:
    - |
      helm upgrade --install matching-engine \
        ./infrastructure/kubernetes/helm/matching-engine \
        --namespace $KUBE_NAMESPACE_STAGING \
        --create-namespace \
        --values ./infrastructure/kubernetes/helm/matching-engine/values-staging.yaml \
        --set image.tag=$CI_COMMIT_SHA \
        --wait \
        --timeout 10m
    - kubectl rollout status deployment/matching-engine -n $KUBE_NAMESPACE_STAGING
    # Run E2E tests
    - apk add --no-cache python3 py3-pip
    - pip3 install pytest requests websockets
    - pytest tests/e2e/ --base-url=https://staging.matching-engine.example.com -v
  only:
    - main

# ============================================
# Deploy to Production
# ============================================

deploy-production:
  stage: deploy-production
  image: alpine/k8s:1.28.3
  environment:
    name: production
    url: https://matching-engine.example.com
  before_script:
    - echo "$KUBECONFIG_PROD" | base64 -d > kubeconfig
    - export KUBECONFIG=./kubeconfig
  script:
    - |
      # Blue-Green deployment logic
      ACTIVE=$(kubectl get service matching-engine-prod -n $KUBE_NAMESPACE_PROD -o jsonpath='{.spec.selector.slot}')
      if [ "$ACTIVE" == "blue" ]; then
        INACTIVE="green"
      else
        INACTIVE="blue"
      fi
      
      echo "Deploying to $INACTIVE slot"
      
      helm upgrade --install matching-engine-$INACTIVE \
        ./infrastructure/kubernetes/helm/matching-engine \
        --namespace $KUBE_NAMESPACE_PROD \
        --values ./infrastructure/kubernetes/helm/matching-engine/values-production.yaml \
        --set image.tag=$CI_COMMIT_TAG \
        --set slot=$INACTIVE \
        --wait \
        --timeout 15m
      
      # Verify deployment
      kubectl rollout status deployment/matching-engine-$INACTIVE -n $KUBE_NAMESPACE_PROD
      
      # Run smoke tests
      kubectl run smoke-test --rm -i --restart=Never \
        --image=curlimages/curl:latest \
        -n $KUBE_NAMESPACE_PROD \
        -- curl -f http://matching-engine-$INACTIVE.$KUBE_NAMESPACE_PROD.svc.cluster.local:8000/health
      
      # Switch traffic
      kubectl patch service matching-engine-prod \
        -n $KUBE_NAMESPACE_PROD \
        --type merge \
        -p "{\"spec\":{\"selector\":{\"slot\":\"$INACTIVE\"}}}"
      
      echo "Deployment successful - switched to $INACTIVE"
  when: manual
  only:
    - tags

6. Kubernetes Deployment Manifests
6.1 Helm Chart Structure
yaml# infrastructure/kubernetes/helm/matching-engine/Chart.yaml
apiVersion: v2
name: matching-engine
description: High-performance cryptocurrency matching engine
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - trading
  - matching-engine
  - cryptocurrency
maintainers:
  - name: Your Name
    email: your.email@example.com
6.2 Base Values (values.yaml)
yaml# infrastructure/kubernetes/helm/matching-engine/values.yaml

# Default values for matching-engine
replicaCount: 2

image:
  repository: ghcr.io/your-org/matching-engine
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  annotations: {}
  name: ""

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
  prometheus.io/path: "/metrics"

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

securityContext:
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

service:
  type: ClusterIP
  ports:
    rest:
      port: 8000
      targetPort: 8000
      protocol: TCP
    websocket:
      port: 8765
      targetPort: 8765
      protocol: TCP
    metrics:
      port: 9090
      targetPort: 9090
      protocol: TCP

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: matching-engine.example.com
      paths:
        - path: /
          pathType: Prefix
          port: 8000
  tls:
    - secretName: matching-engine-tls
      hosts:
        - matching-engine.example.com

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - matching-engine
          topologyKey: kubernetes.io/hostname

# Application configuration
config:
  logLevel: INFO
  database:
    type: postgresql
    host: postgres-service
    port: 5432
    name: matching_engine
  persistence:
    snapshotsEnabled: true
    snapshotInterval: 300
  monitoring:
    metricsEnabled: true

# Environment-specific configurations
env:
  - name: PYTHONUNBUFFERED
    value: "1"
  - name: LOG_LEVEL
    value: INFO

# Secrets (use external secrets operator in production)
secrets:
  database:
    username: postgres
    password: changeme

# Health checks
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

# Persistent storage
persistence:
  enabled: true
  storageClass: "standard"
  accessMode: ReadWriteOnce
  size: 10Gi
  mountPath: /app/data

# PostgreSQL dependency
postgresql:
  enabled: true
  auth:
    username: matching_engine
    password: changeme
    database: matching_engine
  primary:
    persistence:
      enabled: true
      size: 20Gi

# Redis dependency (optional)
redis:
  enabled: false
  auth:
    enabled: true
    password: changeme

# Monitoring
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
6.3 Development Values (values-dev.yaml)
yaml# infrastructure/kubernetes/helm/matching-engine/values-dev.yaml

replicaCount: 1

image:
  pullPolicy: Always

ingress:
  hosts:
    - host: dev.matching-engine.example.com
      paths:
        - path: /
          pathType: Prefix
          port: 8000

resources:
  limits:
    cpu: 1000m
    memory: 2Gi
  requests:
    cpu: 500m
    memory: 1Gi

autoscaling:
  enabled: false

config:
  logLevel: DEBUG
  database:
    host: postgres-dev
    name: matching_engine_dev

env:
  - name: ENVIRONMENT
    value: development
  - name: LOG_LEVEL
    value: DEBUG

postgresql:
  enabled: true
  primary:
    persistence:
      size: 5Gi
6.4 Production Values (values-production.yaml)
yaml# infrastructure/kubernetes/helm/matching-engine/values-production.yaml

replicaCount: 5

image:
  pullPolicy: IfNotPresent
  tag: "" # Set via --set in CD pipeline

ingress:
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
    - host: matching-engine.example.com
      paths:
        - path: /
          pathType: Prefix
          port: 8000

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi

autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 50
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

config:
  logLevel: INFO
  database:
    host: postgres-prod-primary
    name: matching_engine_prod

env:
  - name: ENVIRONMENT
    value: production
  - name: LOG_LEVEL
    value: INFO

# Use external database in production
postgresql:
  enabled: false

# Use external Redis in production
redis:
  enabled: false

# Pod Disruption Budget
podDisruptionBudget:
  enabled: true
  minAvailable: 2

# Network Policy
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress

7. Terraform Infrastructure as Code
7.1 Main Terraform Configuration
hcl# infrastructure/terraform/main.tf

terraform {
  required_version = ">= 1.5"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "matching-engine-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
    encrypt = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  config_path = "~/.kube/config"
  config_context = var.kube_context
}

provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
    config_context = var.kube_context
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    matching_engine = {
      min_size     = 3
      max_size     = 20
      desired_size = 5

      instance_types = ["m5.2xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        workload = "matching-engine"
      }

      taints = []
    }
  }

  tags = var.tags
}

# RDS PostgreSQL
module "db" {
  source = "terraform-aws-modules/rds/aws"

  identifier = "${var.environment}-matching-engine-db"

  engine               = "postgres"
  engine_version       = "15.4"
  family              = "postgres15"
  major_engine_version = "15"
  instance_class       = "db.r5.2xlarge"

  allocated_storage     = 100
  max_allocated_storage = 500

  db_name  = "matching_engine"
  username = "admin"
  port     = 5432

  multi_az               = true
  db_subnet_group_name   = module.vpc.database_subnet_group
  vpc_security_group_ids = [module.security_group.security_group_id]

  backup_retention_period = 30
  backup_window           = "03:00-06:00"
  maintenance_window      = "Mon:00:00-Mon:03:00"

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = var.tags
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.environment}-matching-engine-redis"
  engine               = "redis"
  node_type            = "cache.r5.xlarge"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [module.security_group.security_group_id]

  tags = var.tags
}

# S3 Bucket for Snapshots
resource "aws_s3_bucket" "snapshots" {
  bucket = "${var.environment}-matching-engine-snapshots"

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "snapshots" {
  bucket = aws_s3_bucket.snapshots.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "snapshots" {
  bucket = aws_s3_bucket.snapshots.id

  rule {
    id     = "delete-old-snapshots"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

8. Monitoring & Alerting Configuration
8.1 Prometheus Configuration
yaml# monitoring/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules
rule_files:
  - "alerts.yml"

# Scrape configurations
scrape_configs:
  # Matching Engine metrics
  - job_name: 'matching-engine'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - matching-engine-prod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__

  # Kubernetes cluster metrics
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets:
          - postgres-exporter:9187

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets:
          - redis-exporter:9121
8.2 Alert Rules
yaml# monitoring/prometheus/alerts.yml

groups:
  - name: matching_engine_alerts
    interval: 30s
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
          team: trading
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.99, 
            rate(order_processing_latency_seconds_bucket[5m])
          ) > 0RetryClaude does not have the ability to run the code it generates yet.YContinueyaml.01
        for: 5m
        labels:
          severity: warning
          team: trading
        annotations:
          summary: "High order processing latency"
          description: "P99 latency is {{ $value }}s (threshold: 10ms)"

      # Low Throughput
      - alert: LowThroughput
        expr: |
          rate(orders_submitted_total[5m]) < 10
        for: 10m
        labels:
          severity: warning
          team: trading
        annotations:
          summary: "Low order submission rate"
          description: "Only {{ $value }} orders/sec (expected: >10)"

      # Pod Crashes
      - alert: PodCrashLooping
        expr: |
          rate(kube_pod_container_status_restarts_total{
            namespace="matching-engine-prod"
          }[15m]) > 0
        for: 5m
        labels:
          severity: critical
          team: infrastructure
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.pod }} is restarting frequently"

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: |
          (container_memory_usage_bytes{
            namespace="matching-engine-prod",
            container="matching-engine"
          } / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # High CPU Usage
      - alert: HighCPUUsage
        expr: |
          rate(container_cpu_usage_seconds_total{
            namespace="matching-engine-prod",
            container="matching-engine"
          }[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value | humanizePercentage }}"

      # Database Connection Pool Exhaustion
      - alert: DatabaseConnectionPoolExhausted
        expr: |
          (pg_stat_database_numbackends / pg_settings_max_connections) > 0.9
        for: 5m
        labels:
          severity: critical
          team: database
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Using {{ $value | humanizePercentage }} of connections"

      # Order Book Imbalance
      - alert: OrderBookImbalance
        expr: |
          abs(
            (orderbook_depth{side="bid"} - orderbook_depth{side="ask"}) /
            (orderbook_depth{side="bid"} + orderbook_depth{side="ask"})
          ) > 0.8
        for: 10m
        labels:
          severity: info
          team: trading
        annotations:
          summary: "Significant order book imbalance"
          description: "Book imbalance for {{ $labels.symbol }}: {{ $value | humanizePercentage }}"

      # Wide Spread
      - alert: WideSpread
        expr: |
          spread_basis_points > 100
        for: 5m
        labels:
          severity: warning
          team: trading
        annotations:
          summary: "Wide bid-ask spread"
          description: "Spread for {{ $labels.symbol }} is {{ $value }}bps"

      # Deployment Issues
      - alert: DeploymentReplicasMismatch
        expr: |
          kube_deployment_spec_replicas{
            namespace="matching-engine-prod"
          } != kube_deployment_status_replicas_available{
            namespace="matching-engine-prod"
          }
        for: 10m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Deployment replicas mismatch"
          description: "Expected {{ $value }} replicas but have different count"

      # Disk Space
      - alert: LowDiskSpace
        expr: |
          (node_filesystem_avail_bytes{
            mountpoint="/app/data"
          } / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value | humanizePercentage }} disk space remaining"

      # Trade Execution Stalled
      - alert: TradeExecutionStalled
        expr: |
          rate(trades_executed_total[5m]) == 0 and 
          rate(orders_submitted_total[5m]) > 0
        for: 10m
        labels:
          severity: critical
          team: trading
        annotations:
          summary: "Trade execution appears stalled"
          description: "Orders being submitted but no trades executing"
8.3 Grafana Dashboard JSON
json{
  "dashboard": {
    "title": "Matching Engine - Production Dashboard",
    "panels": [
      {
        "title": "Order Submission Rate",
        "targets": [
          {
            "expr": "rate(orders_submitted_total[5m])",
            "legendFormat": "{{symbol}} - {{side}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Trade Execution Rate",
        "targets": [
          {
            "expr": "rate(trades_executed_total[5m])",
            "legendFormat": "{{symbol}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Order Processing Latency (P50, P95, P99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(order_processing_latency_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(order_processing_latency_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(order_processing_latency_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "type": "graph"
      },
      {
        "title": "HTTP Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "5xx errors"
          },
          {
            "expr": "rate(http_requests_total{status=~\"4..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "4xx errors"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Orders",
        "targets": [
          {
            "expr": "active_orders",
            "legendFormat": "{{symbol}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Order Book Depth",
        "targets": [
          {
            "expr": "orderbook_depth{side=\"bid\"}",
            "legendFormat": "Bids - {{symbol}}"
          },
          {
            "expr": "orderbook_depth{side=\"ask\"}",
            "legendFormat": "Asks - {{symbol}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Spread (Basis Points)",
        "targets": [
          {
            "expr": "spread_basis_points",
            "legendFormat": "{{symbol}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Memory Usage",
        "targets": [
          {
            "expr": "container_memory_usage_bytes{namespace=\"matching-engine-prod\"}",
            "legendFormat": "{{pod}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "CPU Usage",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{namespace=\"matching-engine-prod\"}[5m])",
            "legendFormat": "{{pod}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Pod Restarts",
        "targets": [
          {
            "expr": "kube_pod_container_status_restarts_total{namespace=\"matching-engine-prod\"}",
            "legendFormat": "{{pod}}"
          }
        ],
        "type": "graph"
      }
    ],
    "refresh": "10s",
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}

9. Scripts for CI/CD
9.1 Build Script
bash#!/bin/bash
# scripts/ci/build-image.sh

set -e

echo "🏗️  Building Docker Image..."

# Variables
IMAGE_NAME="${IMAGE_NAME:-matching-engine}"
REGISTRY="${REGISTRY:-ghcr.io}"
VERSION="${VERSION:-$(git rev-parse --short HEAD)}"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"

# Build arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse HEAD)
VERSION_TAG=$(git describe --tags --always)

echo "Building: $FULL_IMAGE"

# Build multi-platform image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VCS_REF="$VCS_REF" \
  --build-arg VERSION="$VERSION_TAG" \
  --tag "$FULL_IMAGE" \
  --tag "${REGISTRY}/${IMAGE_NAME}:latest" \
  --push \
  .

echo "✅ Build complete: $FULL_IMAGE"
9.2 Test Runner Script
bash#!/bin/bash
# scripts/ci/run-tests.sh

set -e

echo "🧪 Running Tests..."

# Setup
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export TESTING=true

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
pip install -q pytest pytest-cov pytest-asyncio pytest-benchmark

# Run linting
echo "🔍 Running linters..."
black --check src/ tests/ || echo "❌ Black formatting issues found"
flake8 src/ tests/ --max-line-length=88 || echo "❌ Flake8 issues found"
mypy src/ --ignore-missing-imports || echo "❌ Type checking issues found"

# Run unit tests
echo "🧪 Running unit tests..."
pytest tests/unit/ \
  -v \
  --cov=src/matching_engine \
  --cov-report=xml \
  --cov-report=html \
  --cov-report=term \
  --junit-xml=pytest-report.xml

# Check coverage threshold
COVERAGE=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
THRESHOLD=80

if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
  echo "❌ Coverage ($COVERAGE%) is below threshold ($THRESHOLD%)"
  exit 1
fi

echo "✅ All tests passed (Coverage: $COVERAGE%)"
9.3 Security Scan Script
bash#!/bin/bash
# scripts/ci/security-scan.sh

set -e

echo "🔒 Running Security Scans..."

# Install security tools
pip install -q bandit safety pip-audit

# Run Bandit (Python security linter)
echo "🔍 Running Bandit..."
bandit -r src/ -f json -o bandit-report.json || true
bandit -r src/ -ll

# Run Safety (dependency vulnerability check)
echo "🔍 Running Safety..."
safety check --json --output safety-report.json || true
safety check

# Run pip-audit
echo "🔍 Running pip-audit..."
pip-audit --desc --output pip-audit-report.json || true
pip-audit --desc

# Scan Docker image if specified
if [ -n "$DOCKER_IMAGE" ]; then
  echo "🔍 Scanning Docker image: $DOCKER_IMAGE"
  
  # Install Trivy
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
  
  # Run Trivy scan
  trivy image \
    --severity HIGH,CRITICAL \
    --format json \
    --output trivy-report.json \
    "$DOCKER_IMAGE"
  
  trivy image \
    --severity HIGH,CRITICAL \
    "$DOCKER_IMAGE"
fi

echo "✅ Security scans complete"
9.4 Deployment Script
bash#!/bin/bash
# scripts/ci/deploy.sh

set -e

# Configuration
ENVIRONMENT="${1:-dev}"
IMAGE_TAG="${2:-latest}"
NAMESPACE="matching-engine-${ENVIRONMENT}"
HELM_RELEASE="matching-engine"
HELM_CHART="./infrastructure/kubernetes/helm/matching-engine"

echo "🚀 Deploying to ${ENVIRONMENT} environment..."
echo "   Image: ${IMAGE_TAG}"
echo "   Namespace: ${NAMESPACE}"

# Validate kubectl connection
if ! kubectl cluster-info &> /dev/null; then
  echo "❌ Cannot connect to Kubernetes cluster"
  exit 1
fi

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm
echo "📦 Deploying with Helm..."
helm upgrade --install "$HELM_RELEASE" "$HELM_CHART" \
  --namespace "$NAMESPACE" \
  --values "${HELM_CHART}/values-${ENVIRONMENT}.yaml" \
  --set image.tag="$IMAGE_TAG" \
  --set image.pullPolicy=Always \
  --wait \
  --timeout 10m \
  --atomic \
  --cleanup-on-fail

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/matching-engine \
  -n "$NAMESPACE" \
  --timeout=10m

# Run health check
echo "🏥 Running health check..."
SERVICE_URL=$(kubectl get ingress matching-engine \
  -n "$NAMESPACE" \
  -o jsonpath='{.spec.rules[0].host}')

if [ -n "$SERVICE_URL" ]; then
  for i in {1..30}; do
    if curl -sf "https://${SERVICE_URL}/health" > /dev/null; then
      echo "✅ Health check passed"
      break
    fi
    echo "⏳ Waiting for service to be ready... ($i/30)"
    sleep 10
  done
fi

# Get deployment info
echo ""
echo "📊 Deployment Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   Namespace: $NAMESPACE"
echo "   Image: $IMAGE_TAG"
echo "   URL: https://${SERVICE_URL}"
echo ""
kubectl get pods -n "$NAMESPACE" -l app=matching-engine

echo "✅ Deployment complete!"

10. Local Development Setup
10.1 Local Development Script
bash#!/bin/bash
# scripts/local-dev/setup.sh

set -e

echo "🔧 Setting up local development environment..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed."; exit 1; }

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[dev]"

# Setup pre-commit hooks
echo "🪝 Setting up git hooks..."
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run checks before commit
black --check src/ tests/
flake8 src/ tests/
mypy src/
pytest tests/unit/ -q
EOF
chmod +x .git/hooks/pre-commit

# Start local services
echo "🐳 Starting local services with Docker Compose..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🗄️  Running database migrations..."
python -m src.matching_engine.db.migrate

# Create test data
echo "📊 Creating test data..."
python scripts/local-dev/seed-data.py

echo ""
echo "✅ Local development environment ready!"
echo ""
echo "   API: http://localhost:8000"
echo "   WebSocket: ws://localhost:8765"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "Run 'source venv/bin/activate' to activate the virtual environment"
echo "Run 'python -m src.matching_engine.main' to start the application"
10.2 Docker Compose for Local Development
yaml# docker-compose.dev.yml

version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: matching_engine_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # HTTP collector
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411

volumes:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

11. Testing in CI/CD
11.1 Load Test Script (k6)
javascript// tests/performance/load-test.js

import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const orderSubmissionRate = new Rate('order_submission_success');
const orderLatency = new Trend('order_submission_latency');
const tradeCount = new Counter('trades_received');

// Test configuration
export const options = {
  stages: [
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 200 },  // Peak at 200 users
    { duration: '2m', target: 100 },  // Ramp down
    { duration: '1m', target: 0 },    // Cool down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    'http_req_failed': ['rate<0.01'],                  // Error rate < 1%
    'order_submission_success': ['rate>0.95'],         // Success rate > 95%
    'order_submission_latency': ['p(95)<200'],         // P95 < 200ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8765';

// Test data
const symbols = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT'];
const orderTypes = ['limit', 'market', 'ioc'];
const sides = ['buy', 'sell'];

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomPrice(base) {
  return (base + (Math.random() - 0.5) * base * 0.01).toFixed(2);
}

// Main test scenario
export default function () {
  const symbol = randomChoice(symbols);
  const orderType = randomChoice(orderTypes);
  const side = randomChoice(sides);
  const basePrice = 45000;
  
  // Submit order via REST API
  const orderPayload = JSON.stringify({
    symbol: symbol,
    order_type: orderType,
    side: side,
    quantity: (Math.random() * 0.5 + 0.1).toFixed(8),
    price: orderType === 'market' ? undefined : randomPrice(basePrice),
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
    tags: { name: 'SubmitOrder' },
  };

  const start = Date.now();
  const response = http.post(`${BASE_URL}/api/v1/orders`, orderPayload, params);
  const duration = Date.now() - start;

  // Record metrics
  const success = check(response, {
    'status is 200/201': (r) => r.status === 200 || r.status === 201,
    'has order_id': (r) => JSON.parse(r.body).order_id !== undefined,
    'response time OK': () => duration < 1000,
  });

  orderSubmissionRate.add(success);
  orderLatency.add(duration);

  // Get order book occasionally
  if (Math.random() < 0.1) {
    const bookResponse = http.get(`${BASE_URL}/api/v1/orderbook/${symbol}`, {
      tags: { name: 'GetOrderBook' },
    });
    
    check(bookResponse, {
      'book status is 200': (r) => r.status === 200,
      'book has bids/asks': (r) => {
        const body = JSON.parse(r.body);
        return body.bids !== undefined && body.asks !== undefined;
      },
    });
  }

  sleep(Math.random() * 2 + 1); // Random sleep 1-3 seconds
}

// WebSocket test scenario
export function websocketScenario() {
  const symbol = randomChoice(symbols);
  const url = `${WS_URL}`;

  const response = ws.connect(url, function (socket) {
    socket.on('open', () => {
      // Subscribe to trades
      socket.send(JSON.stringify({
        action: 'subscribe',
        channel: 'trades',
        symbol: symbol,
      }));

      // Subscribe to order book
      socket.send(JSON.stringify({
        action: 'subscribe',
        channel: 'orderbook',
        symbol: symbol,
      }));
    });

    socket.on('message', (data) => {
      const message = JSON.parse(data);
      
      if (message.type === 'trade') {
        tradeCount.add(1);
      }
      
      check(message, {
        'valid message type': (m) => ['trade', 'orderbook', 'snapshot'].includes(m.type),
        'has timestamp': (m) => m.timestamp !== undefined,
      });
    });

    socket.on('error', (e) => {
      console.log('WebSocket error:', e);
    });

    // Keep connection open for 30 seconds
    socket.setTimeout(() => {
      socket.close();
    }, 30000);
  });

  check(response, {
    'ws connection successful': (r) => r && r.status === 101,
  });
}

// Handle setup and teardown
export function setup() {
  // Warm up the system
  console.log('Warming up system...');
  for (let i = 0; i < 10; i++) {
    http.get(`${BASE_URL}/health`);
  }
  return { startTime: Date.now() };
}

export function teardown(data) {
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`Test completed in ${duration} seconds`);
}
11.2 E2E Test Suite
python# tests/e2e/test_full_flow.py

import pytest
import asyncio
import httpx
import websockets
import json
from decimal import Decimal
from typing import List, Dict

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8765"

@pytest.mark.asyncio
class TestFullTradingFlow:
    """End-to-end tests for complete trading workflow"""
    
    async def test_order_submission_and_matching(self):
        """Test full order lifecycle from submission to execution"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Submit buy limit order
            buy_order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
                "price": "45000.00"
            })
            assert buy_order.status_code in [200, 201]
            buy_data = buy_order.json()
            assert "order_id" in buy_data
            buy_order_id = buy_data["order_id"]
            
            # Verify order on book
            book = await client.get("/api/v1/orderbook/BTC-USDT")
            assert book.status_code == 200
            book_data = book.json()
            assert len(book_data["bids"]) > 0
            
            # Submit matching sell order
            sell_order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "quantity": "1.0",
                "price": "45000.00"
            })
            assert sell_order.status_code in [200, 201]
            sell_data = sell_order.json()
            
            # Verify both orders filled
            assert sell_data["status"] == "filled"
            await asyncio.sleep(0.5)  # Allow time for processing
            
            # Check order book updated
            book_after = await client.get("/api/v1/orderbook/BTC-USDT")
            book_after_data = book_after.json()
            # Order should be removed from book
    
    async def test_websocket_market_data_stream(self):
        """Test WebSocket market data streaming"""
        
        messages_received = []
        
        async with websockets.connect(WS_URL) as ws:
            # Subscribe to order book
            await ws.send(json.dumps({
                "action": "subscribe",
                "channel": "orderbook",
                "symbol": "BTC-USDT"
            }))
            
            # Receive initial snapshot
            snapshot = await asyncio.wait_for(ws.recv(), timeout=5.0)
            snapshot_data = json.loads(snapshot)
            assert snapshot_data["type"] == "snapshot"
            assert "bids" in snapshot_data
            assert "asks" in snapshot_data
            
            # Submit order to trigger update
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                await client.post("/api/v1/orders", json={
                    "symbol": "BTC-USDT",
                    "order_type": "limit",
                    "side": "buy",
                    "quantity": "0.5",
                    "price": "44900.00"
                })
            
            # Receive update
            update = await asyncio.wait_for(ws.recv(), timeout=5.0)
            update_data = json.loads(update)
            assert update_data["type"] == "orderbook"
            assert update_data["symbol"] == "BTC-USDT"
    
    async def test_websocket_trade_stream(self):
        """Test WebSocket trade execution streaming"""
        
        async with websockets.connect(WS_URL) as ws:
            # Subscribe to trades
            await ws.send(json.dumps({
                "action": "subscribe",
                "channel": "trades",
                "symbol": "BTC-USDT"
            }))
            
            # Submit orders that will match
            async with httpx.AsyncClient(base_url=BASE_URL) as client:
                # Buy order
                await client.post("/api/v1/orders", json={
                    "symbol": "BTC-USDT",
                    "order_type": "limit",
                    "side": "buy",
                    "quantity": "0.1",
                    "price": "45100.00"
                })
                
                # Matching sell order
                await client.post("/api/v1/orders", json={
                    "symbol": "BTC-USDT",
                    "order_type": "limit",
                    "side": "sell",
                    "quantity": "0.1",
                    "price": "45100.00"
                })
            
            # Receive trade execution
            trade = await asyncio.wait_for(ws.recv(), timeout=5.0)
            trade_data = json.loads(trade)
            assert trade_data["type"] == "trade"
            assert trade_data["symbol"] == "BTC-USDT"
            assert "trade_id" in trade_data
            assert "price" in trade_data
            assert "quantity" in trade_data
    
    async def test_order_cancellation(self):
        """Test order cancellation workflow"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Submit order
            order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
                "price": "RetryClaude does not have the ability to run the code it generates yet.YContinuepython"40000.00"  # Far from market
            })
            assert order.status_code in [200, 201]
            order_data = order.json()
            order_id = order_data["order_id"]
            
            # Cancel order
            cancel_response = await client.delete(
                f"/api/v1/orders/{order_id}",
                params={"symbol": "BTC-USDT"}
            )
            assert cancel_response.status_code == 200
            cancel_data = cancel_response.json()
            assert cancel_data["status"] == "cancelled"
            
            # Verify order removed from book
            book = await client.get("/api/v1/orderbook/BTC-USDT")
            book_data = book.json()
            # Order should not be in book
    
    async def test_ioc_order_execution(self):
        """Test Immediate-Or-Cancel order behavior"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Submit IOC order with no matching liquidity
            ioc_order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "ioc",
                "side": "buy",
                "quantity": "10.0",
                "price": "40000.00"  # No liquidity at this price
            })
            assert ioc_order.status_code in [200, 201]
            ioc_data = ioc_order.json()
            assert ioc_data["status"] == "cancelled"
            assert ioc_data["filled_quantity"] == "0"
    
    async def test_fok_order_execution(self):
        """Test Fill-Or-Kill order behavior"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Add limited liquidity
            await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "quantity": "0.5",
                "price": "45000.00"
            })
            
            # Try FOK for more than available
            fok_order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "fok",
                "side": "buy",
                "quantity": "1.0",  # More than available
                "price": "45000.00"
            })
            assert fok_order.status_code in [200, 201]
            fok_data = fok_order.json()
            assert fok_data["status"] == "cancelled"
            assert fok_data["filled_quantity"] == "0"
    
    async def test_market_order_execution(self):
        """Test market order immediate execution"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Add liquidity
            await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "quantity": "1.0",
                "price": "45000.00"
            })
            
            # Submit market order
            market_order = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "market",
                "side": "buy",
                "quantity": "0.5"
            })
            assert market_order.status_code in [200, 201]
            market_data = market_order.json()
            assert market_data["status"] in ["filled", "partial"]
            assert float(market_data["filled_quantity"]) > 0
    
    async def test_concurrent_orders(self):
        """Test system under concurrent order load"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Submit multiple orders concurrently
            tasks = []
            for i in range(100):
                side = "buy" if i % 2 == 0 else "sell"
                price = 45000 + (i % 10)
                
                task = client.post("/api/v1/orders", json={
                    "symbol": "BTC-USDT",
                    "order_type": "limit",
                    "side": side,
                    "quantity": "0.1",
                    "price": str(price)
                })
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all succeeded
            success_count = sum(
                1 for r in responses 
                if not isinstance(r, Exception) and r.status_code in [200, 201]
            )
            assert success_count >= 95  # At least 95% success rate
    
    async def test_price_time_priority(self):
        """Test price-time priority enforcement"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Submit orders at same price (FIFO)
            order1 = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
                "price": "45000.00"
            })
            order1_id = order1.json()["order_id"]
            
            await asyncio.sleep(0.1)  # Ensure time difference
            
            order2 = await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "buy",
                "quantity": "1.0",
                "price": "45000.00"
            })
            order2_id = order2.json()["order_id"]
            
            # Submit partial matching order
            await client.post("/api/v1/orders", json={
                "symbol": "BTC-USDT",
                "order_type": "limit",
                "side": "sell",
                "quantity": "0.5",
                "price": "45000.00"
            })
            
            # First order should be partially filled, second untouched
            # (Would need order status endpoint to verify)
    
    async def test_health_and_metrics(self):
        """Test health check and metrics endpoints"""
        
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            # Health check
            health = await client.get("/health")
            assert health.status_code == 200
            health_data = health.json()
            assert health_data["status"] == "healthy"
            
            # Metrics endpoint
            metrics = await client.get("/metrics")
            assert metrics.status_code == 200
            assert "orders_submitted_total" in metrics.text
            assert "trades_executed_total" in metrics.text

12. Environment Configuration Management
12.1 Environment Variables Template
bash# .env.template
# Copy this to .env and fill in actual values

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WEBSOCKET_PORT=8765
METRICS_PORT=9090

# Database
DATABASE_TYPE=postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=matching_engine
DATABASE_USER=postgres
DATABASE_PASSWORD=changeme
DATABASE_POOL_SIZE=20

# Redis (optional)
REDIS_ENABLED=false
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=changeme

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_SECOND=100
RATE_LIMIT_BURST_SIZE=200

# Feature Flags
FEES_ENABLED=false
MAKER_FEE_BPS=10
TAKER_FEE_BPS=20

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=
JAEGER_ENABLED=false
JAEGER_ENDPOINT=http://jaeger:14268/api/traces

# AWS (if using cloud services)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_SNAPSHOTS=matching-engine-snapshots

# Kubernetes (if using K8s)
KUBERNETES_NAMESPACE=matching-engine-dev
KUBERNETES_SERVICE_ACCOUNT=matching-engine

# Alert Configuration
SLACK_WEBHOOK_URL=
PAGERDUTY_INTEGRATION_KEY=
12.2 Configuration Loader
python# src/matching_engine/config.py

import os
from typing import Optional
from pydantic import BaseSettings, Field, validator
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseType(str, Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

class Settings(BaseSettings):
    """Application configuration"""
    
    # Application
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    websocket_port: int = Field(default=8765)
    metrics_port: int = Field(default=9090)
    
    # Database
    database_type: DatabaseType = Field(default=DatabaseType.POSTGRESQL)
    database_host: str = Field(default="localhost")
    database_port: int = Field(default=5432)
    database_name: str = Field(default="matching_engine")
    database_user: str = Field(default="postgres")
    database_password: str = Field(default="changeme")
    database_pool_size: int = Field(default=20)
    
    # Redis
    redis_enabled: bool = Field(default=False)
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = None
    
    # Security
    secret_key: str = Field(default="dev-secret-key")
    jwt_secret: str = Field(default="dev-jwt-secret")
    allowed_origins: list[str] = Field(default=["http://localhost:3000"])
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests_per_second: int = Field(default=100)
    rate_limit_burst_size: int = Field(default=200)
    
    # Features
    fees_enabled: bool = Field(default=False)
    maker_fee_bps: int = Field(default=10)
    taker_fee_bps: int = Field(default=20)
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True)
    sentry_dsn: Optional[str] = None
    jaeger_enabled: bool = Field(default=False)
    jaeger_endpoint: Optional[str] = None
    
    # AWS
    aws_region: str = Field(default="us-east-1")
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket_snapshots: Optional[str] = None
    
    # Kubernetes
    kubernetes_namespace: str = Field(default="default")
    kubernetes_service_account: str = Field(default="default")
    
    # Alerts
    slack_webhook_url: Optional[str] = None
    pagerduty_integration_key: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """Construct database URL"""
        if self.database_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.database_name}.db"
        else:
            return (
                f"postgresql://{self.database_user}:{self.database_password}"
                f"@{self.database_host}:{self.database_port}/{self.database_name}"
            )
    
    @property
    def redis_url(self) -> Optional[str]:
        """Construct Redis URL"""
        if not self.redis_enabled:
            return None
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    @validator('allowed_origins', pre=True)
    def parse_origins(cls, v):
        """Parse comma-separated origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('secret_key', 'jwt_secret')
    def validate_secrets(cls, v, field):
        """Validate secrets in production"""
        if os.getenv('ENVIRONMENT') == 'production':
            if v in ['dev-secret-key', 'dev-jwt-secret']:
                raise ValueError(f"{field.name} must be set in production")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Singleton instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

# Export for convenience
settings = get_settings()

13. Deployment Runbook
13.1 Pre-Deployment Checklist
markdown# Pre-Deployment Checklist

## Code Quality
- [ ] All CI/CD tests passing
- [ ] Code coverage > 80%
- [ ] Security scans completed with no critical issues
- [ ] Performance tests meeting SLAs
- [ ] Load tests completed successfully

## Configuration
- [ ] Environment variables configured
- [ ] Secrets properly stored (HashiCorp Vault, AWS Secrets Manager)
- [ ] Database migrations prepared
- [ ] Feature flags configured

## Infrastructure
- [ ] Kubernetes cluster health verified
- [ ] Database backup completed
- [ ] Monitoring dashboards configured
- [ ] Alert rules tested
- [ ] Log aggregation working

## Documentation
- [ ] CHANGELOG updated
- [ ] API documentation updated
- [ ] Runbook updated
- [ ] Architecture diagrams current

## Communication
- [ ] Stakeholders notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan documented
- [ ] On-call engineer identified

## Backup & Recovery
- [ ] Current production state backed up
- [ ] Recovery procedures tested
- [ ] Rollback scripts prepared
13.2 Deployment Steps
markdown# Deployment Procedure

## 1. Pre-Deployment (T-30 minutes)
````bash
# Verify current state
kubectl get pods -n matching-engine-prod
kubectl get deployments -n matching-engine-prod

# Check resource utilization
kubectl top nodes
kubectl top pods -n matching-engine-prod

# Verify database connection
psql -h prod-db.example.com -U admin -d matching_engine -c "SELECT 1"

# Create backup
kubectl exec -n matching-engine-prod postgres-0 -- \
  pg_dump -U admin matching_engine > backup-$(date +%Y%m%d-%H%M%S).sql
````

## 2. Deployment (T-0)
````bash
# Set version
export VERSION=v1.2.3
export IMAGE_TAG=ghcr.io/your-org/matching-engine:${VERSION}

# Deploy to inactive slot (blue-green)
./scripts/ci/deploy.sh production ${VERSION}

# Monitor deployment
kubectl rollout status deployment/matching-engine-green -n matching-engine-prod

# Verify health
curl -f https://green.matching-engine.example.com/health
````

## 3. Smoke Tests (T+5 minutes)
````bash
# Run smoke tests
pytest tests/e2e/smoke/ \
  --base-url=https://green.matching-engine.example.com

# Check metrics
curl -s https://green.matching-engine.example.com/metrics | grep orders_submitted_total
````

## 4. Traffic Switch (T+10 minutes)
````bash
# Gradual traffic shift
# 10% traffic
kubectl patch service matching-engine-prod \
  -n matching-engine-prod \
  --type merge \
  -p '{"spec":{"selector":{"slot":"green","weight":"10"}}}'

# Monitor for 5 minutes
watch -n 10 "curl -s http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=rate(http_requests_total{status=~\"5..\"}[5m])'"

# 50% traffic
kubectl patch service matching-engine-prod \
  -n matching-engine-prod \
  --type merge \
  -p '{"spec":{"selector":{"slot":"green","weight":"50"}}}'

# Monitor for 10 minutes

# 100% traffic
kubectl patch service matching-engine-prod \
  -n matching-engine-prod \
  --type merge \
  -p '{"spec":{"selector":{"slot":"green"}}}'
````

## 5. Post-Deployment Validation (T+30 minutes)
````bash
# Run full E2E tests
pytest tests/e2e/production-safe/ -v

# Verify metrics
curl -s https://matching-engine.example.com/metrics

# Check logs
kubectl logs -n matching-engine-prod -l app=matching-engine --tail=100

# Verify database
psql -h prod-db.example.com -U admin -d matching_engine -c \
  "SELECT COUNT(*) FROM trades WHERE created_at > NOW() - INTERVAL '1 hour'"
````

## 6. Cleanup (T+2 hours)
````bash
# Keep blue deployment for 24h for potential rollback
# Delete after verification period
# helm delete matching-engine-blue -n matching-engine-prod
````

### 13.3 Rollback Procedure
````markdown
# Rollback Procedure

## Immediate Rollback (< 5 minutes)
```bash
# Switch traffic back to blue slot
kubectl patch service matching-engine-prod \
  -n matching-engine-prod \
  --type merge \
  -p '{"spec":{"selector":{"slot":"blue"}}}'

# Verify traffic switched
curl -f https://matching-engine.example.com/health

# Delete failed deployment
helm delete matching-engine-green -n matching-engine-prod
```

## Database Rollback (if needed)
```bash
# Restore from backup
psql -h prod-db.example.com -U admin -d matching_engine < backup-TIMESTAMP.sql

# Verify data
psql -h prod-db.example.com -U admin -d matching_engine -c \
  "SELECT MAX(created_at) FROM trades"
```

## Post-Rollback
```bash
# Notify stakeholders
# Update incident report
# Schedule post-mortem
```
````

---

## 14. Summary

This comprehensive CI/CD pipeline provides:

### ✅ **Complete Automation**
- **GitHub Actions**: Full CI/CD with quality gates
- **GitLab CI**: Alternative platform support
- **Automated Testing**: Unit, integration, E2E, performance
- **Security Scanning**: Container, dependency, code analysis

### ✅ **Multi-Environment Strategy**
- **Development**: Auto-deploy on feature branches
- **Staging**: Auto-deploy on main, full testing
- **Production**: Manual approval, blue-green deployment

### ✅ **Safety & Reliability**
- **Blue-Green Deployments**: Zero-downtime releases
- **Canary Analysis**: Gradual traffic shifting
- **Automated Rollback**: Quick recovery from failures
- **Health Checks**: Continuous validation

### ✅ **Observability**
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Alerting**: Proactive issue detection
- **Distributed Tracing**: Jaeger integration

### ✅ **Infrastructure as Code**
- **Terraform**: Cloud infrastructure
- **Helm Charts**: Kubernetes deployments
- **Kustomize**: Environment-specific configs
- **Docker**: Containerization

### 🎯 **Key Benefits**

1. **Deployment-First Development**: Test every feature in production-like environment
2. **Continuous Feedback**: Immediate visibility into code quality and performance
3. **Risk Mitigation**: Multiple safety gates and rollback mechanisms
4. **Developer Productivity**: Automated repetitive tasks
5. **Production Confidence**: Comprehensive testing at every stage

### 📊 **Pipeline Execution Times**

- **CI Pipeline**: 10-15 minutes
- **Deploy to Dev**: 3-5 minutes
- **Deploy to Staging**: 8-12 minutes
- **Deploy to Production**: 20-30 minutes (with canary)

This pipeline enables you to:
- Deploy to dev environment **within 20 minutes** of pushing code
- Have **full confidence** in production deployments
- **Rollback in < 5 minutes** if issues arise
- **Monitor and alert** on all critical metrics

You can now start coding with the peace of mind that every change will be automatically tested, validated, and safely deployed! 🚀