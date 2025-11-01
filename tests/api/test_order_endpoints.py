"""
Tests for Order API Endpoints
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient

from src.api.main import app
from src.matching_engine.config.database import init_db


class TestOrderEndpoints:
    """Test order API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup test database"""
        init_db(database_url="sqlite:///:memory:", echo=False)
        
        # Reset global instances in routers
        import src.api.routers.orders as orders_module
        orders_module._matching_engine = None
        orders_module._order_manager = None
        orders_module._trade_manager = None
        orders_module._order_repository = None
        
        yield
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_submit_limit_order(self, client):
        """Test submitting a limit order"""
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5",
            "time_in_force": "GTC"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "alice"
        assert data["symbol"] == "BTC-USD"
        assert data["side"].lower() == "buy"
        assert data["order_type"].lower() == "limit"
        assert data["price"] == "50000.00"
        assert data["quantity"] == "1.5"
        assert data["status"].lower() == "open"
        assert "order_id" in data
    
    def test_submit_market_order(self, client):
        """Test submitting a market order"""
        order_data = {
            "user_id": "bob",
            "symbol": "BTC-USD",
            "side": "sell",
            "order_type": "market",
            "quantity": "1.0"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "bob"
        assert data["order_type"].lower() == "market"
        assert data["price"] is None
    
    def test_submit_limit_order_without_price(self, client):
        """Test submitting limit order without price fails"""
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "quantity": "1.5"
        }
        
        response = client.post("/api/v1/orders", json=order_data)
        
        assert response.status_code == 400
        assert "price" in response.json()["detail"].lower()
    
    def test_get_order(self, client):
        """Test getting order by ID"""
        # First submit an order
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5"
        }
        
        submit_response = client.post("/api/v1/orders", json=order_data)
        order_id = submit_response.json()["order_id"]
        
        # Get the order
        response = client.get(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["user_id"] == "alice"
    
    def test_get_nonexistent_order(self, client):
        """Test getting non-existent order returns 404"""
        response = client.get("/api/v1/orders/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_list_orders(self, client):
        """Test listing orders"""
        # Submit multiple orders
        for i in range(3):
            order_data = {
                "user_id": f"user{i}",
                "symbol": "BTC-USD",
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.0"
            }
            client.post("/api/v1/orders", json=order_data)
        
        # List all orders
        response = client.get("/api/v1/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert len(data["orders"]) >= 3
        assert data["total"] >= 3
    
    def test_list_orders_by_user(self, client):
        """Test listing orders filtered by user"""
        # Submit orders for different users
        for user in ["alice", "bob", "alice"]:
            order_data = {
                "user_id": user,
                "symbol": "BTC-USD",
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.0"
            }
            client.post("/api/v1/orders", json=order_data)
        
        # List alice's orders
        response = client.get("/api/v1/orders?user_id=alice")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) >= 2
        assert all(o["user_id"] == "alice" for o in data["orders"])
    
    def test_list_orders_by_symbol(self, client):
        """Test listing orders filtered by symbol"""
        # Submit orders for different symbols
        for symbol in ["BTC-USD", "ETH-USD", "BTC-USD"]:
            order_data = {
                "user_id": "alice",
                "symbol": symbol,
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.0"
            }
            client.post("/api/v1/orders", json=order_data)
        
        # List BTC-USD orders
        response = client.get("/api/v1/orders?symbol=BTC-USD")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) >= 2
        assert all(o["symbol"] == "BTC-USD" for o in data["orders"])
    
    def test_cancel_order(self, client):
        """Test cancelling an order"""
        # Submit an order
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5"
        }
        
        submit_response = client.post("/api/v1/orders", json=order_data)
        order_id = submit_response.json()["order_id"]
        
        # Cancel the order
        response = client.delete(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["status"] == "cancelled"
    
    def test_cancel_nonexistent_order(self, client):
        """Test cancelling non-existent order returns 404"""
        response = client.delete("/api/v1/orders/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_amend_order_price(self, client):
        """Test amending order price"""
        # Submit an order
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5"
        }
        
        submit_response = client.post("/api/v1/orders", json=order_data)
        order_id = submit_response.json()["order_id"]
        
        # Amend the order
        amend_data = {"price": "51000.00"}
        response = client.put(f"/api/v1/orders/{order_id}", json=amend_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["price"] == "51000.00"
    
    def test_amend_order_quantity(self, client):
        """Test amending order quantity"""
        # Submit an order
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5"
        }
        
        submit_response = client.post("/api/v1/orders", json=order_data)
        order_id = submit_response.json()["order_id"]
        
        # Amend the order
        amend_data = {"quantity": "2.0"}
        response = client.put(f"/api/v1/orders/{order_id}", json=amend_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["quantity"] == "2.0"
    
    def test_amend_order_without_fields(self, client):
        """Test amending order without fields fails"""
        # Submit an order
        order_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.5"
        }
        
        submit_response = client.post("/api/v1/orders", json=order_data)
        order_id = submit_response.json()["order_id"]
        
        # Try to amend without fields
        response = client.put(f"/api/v1/orders/{order_id}", json={})
        
        assert response.status_code == 400
    
    def test_get_active_orders(self, client):
        """Test getting active orders"""
        # Submit and cancel some orders
        order_ids = []
        for i in range(3):
            order_data = {
                "user_id": "alice",
                "symbol": "BTC-USD",
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.0"
            }
            response = client.post("/api/v1/orders", json=order_data)
            order_ids.append(response.json()["order_id"])
        
        # Cancel one order
        client.delete(f"/api/v1/orders/{order_ids[0]}")
        
        # Get active orders
        response = client.get("/api/v1/orders/active/all")
        
        assert response.status_code == 200
        data = response.json()
        # Should have 2 active orders (3 submitted - 1 cancelled)
        assert len(data["orders"]) >= 2
        assert all(o["status"] in ["open", "partially_filled"] for o in data["orders"])
    
    def test_matching_orders(self, client):
        """Test that matching orders execute trades"""
        # Submit buy order
        buy_data = {
            "user_id": "alice",
            "symbol": "BTC-USD",
            "side": "buy",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.0"
        }
        buy_response = client.post("/api/v1/orders", json=buy_data)
        assert buy_response.status_code == 201
        
        # Submit matching sell order
        sell_data = {
            "user_id": "bob",
            "symbol": "BTC-USD",
            "side": "sell",
            "order_type": "limit",
            "price": "50000.00",
            "quantity": "1.0"
        }
        sell_response = client.post("/api/v1/orders", json=sell_data)
        assert sell_response.status_code == 201
        
        # Both orders should be filled
        sell_data = sell_response.json()
        assert sell_data["status"] in ["filled", "partially_filled"]
