# Cryptocurrency Matching Engine

A high-performance cryptocurrency matching engine built with Python, implementing REG NMS-inspired principles with microsecond-level latency targets.

## 🚀 Features

- **Price-Time Priority Matching**: Fair order execution following industry standards
- **Multiple Order Types**: Market, Limit, IOC (Immediate-Or-Cancel), FOK (Fill-Or-Kill)
- **Real-time Market Data**: WebSocket streaming for order book updates and trade executions
- **High Performance**: Optimized for low-latency order processing
- **Production Ready**: Complete CI/CD pipeline with automated testing and deployment
- **Observability**: Built-in Prometheus metrics and Grafana dashboards

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## 🛠️ Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd matching-engine
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Start services with Docker Compose**
```bash
docker-compose up -d
```

5. **Access the application**
- REST API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- WebSocket: ws://localhost:8765
- Prometheus: http://localhost:9091
- Grafana: http://localhost:3000 (admin/admin)

## 🏗️ Architecture

The matching engine follows a modular architecture:

```
src/matching_engine/
├── core/           # Core matching engine logic
├── api/            # REST and WebSocket APIs
├── models/         # Data models
├── services/       # Business logic services
└── utils/          # Utility functions
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/matching_engine --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

## 📊 Monitoring

Access Grafana dashboards at http://localhost:3000:
- Order processing metrics
- Latency percentiles
- Order book depth
- System health

## 🚢 Deployment

### CI/CD Pipeline

The project includes a complete CI/CD pipeline with GitHub Actions:

1. **Code Quality**: Linting, formatting, type checking
2. **Testing**: Unit, integration, and security tests
3. **Build**: Docker image creation and scanning
4. **Deploy**: Automated deployment to dev/staging/production

### Manual Deployment

```bash
# Build Docker image
docker build -t matching-engine:latest .

# Run container
docker run -p 8000:8000 -p 8765:8765 matching-engine:latest
```

## 📖 API Documentation

### REST API

**Submit Order**
```bash
POST /api/v1/orders
Content-Type: application/json

{
  "symbol": "BTC-USDT",
  "order_type": "limit",
  "side": "buy",
  "quantity": "0.5",
  "price": "45000.00"
}
```

**Get Order Status**
```bash
GET /api/v1/orders/{order_id}
```

**Cancel Order**
```bash
DELETE /api/v1/orders/{order_id}
```

### WebSocket API

**Subscribe to Order Book**
```javascript
{
  "action": "subscribe",
  "channel": "orderbook",
  "symbol": "BTC-USDT",
  "depth": 10
}
```

**Subscribe to Trades**
```javascript
{
  "action": "subscribe",
  "channel": "trades",
  "symbol": "BTC-USDT"
}
```

## 🔧 Configuration

Configuration is managed through environment variables:

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/matching_engine

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
WS_PORT=8765
```

## 📈 Performance Targets

- **Order Processing**: 1,000-5,000 orders/sec
- **Matching Latency**: P99 < 10ms
- **API Response Time**: P99 < 100ms
- **WebSocket Latency**: < 50ms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `/docs`
- Review the architecture design document

## 🗺️ Roadmap

- [x] Phase 0: CI/CD Pipeline Setup
- [ ] Phase 1: Core Engine Foundation
- [ ] Phase 2: Order Management
- [ ] Phase 3: Trade Generation & Execution
- [ ] Phase 4: API Layer
- [ ] Phase 5: Persistence & Recovery
- [ ] Phase 6: Performance Optimization
- [ ] Phase 7: Monitoring & Observability
- [ ] Phase 8: Advanced Features
