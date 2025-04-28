from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import pandas as pd
import json
import datetime
import asyncio
from contextlib import asynccontextmanager

# Import our models and prediction engine
from database_models import Base, Product, ProfitGroup, Sale, SaleItem, Customer, PricingRule, StoreStatus
from sales_prediction_model import SalesPredictionModel

# Database setup
DATABASE_URL = "sqlite:///./pos_system.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize prediction model
prediction_model = SalesPredictionModel()
model_trained = False

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize FastAPI app
app = FastAPI(title="Small Business POS API with Dynamic Pricing")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create connection manager
manager = ConnectionManager()


# API endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the Small Business POS API"}

# Product endpoints
@app.post("/products/")
def create_product(name: str, sku: str, cost_price: float, base_price: float, 
                   stock_quantity: int, description: Optional[str] = None, db: Session = Depends(get_db)):
    """Create a new product."""
    db_product = Product(
        name=name,
        sku=sku,
        description=description,
        cost_price=cost_price,
        base_price=base_price,
        current_price=base_price,  # Initially set to base price
        stock_quantity=stock_quantity
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/")
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all products."""
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}")
def read_product(product_id: int, db: Session = Depends(get_db)):
    """Get a specific product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}")
def update_product(product_id: int, name: Optional[str] = None, cost_price: Optional[float] = None,
                  base_price: Optional[float] = None, stock_quantity: Optional[int] = None,
                  description: Optional[str] = None, db: Session = Depends(get_db)):
    """Update a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if name:
        product.name = name
    if cost_price is not None:
        product.cost_price = cost_price
    if base_price is not None:
        product.base_price = base_price
        # Also update current price if base price changes
        product.current_price = calculate_dynamic_price(db, product)
    if stock_quantity is not None:
        product.stock_quantity = stock_quantity
    if description:
        product.description = description
    
    db.commit()
    db.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# Profit Group endpoints
@app.post("/profit-groups/")
def create_profit_group(name: str, min_profit_price: float, db: Session = Depends(get_db)):
    """Create a new profit group."""
    db_group = ProfitGroup(
        name=name,
        min_profit_price=min_profit_price
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.get("/profit-groups/")
def read_profit_groups(db: Session = Depends(get_db)):
    """Get all profit groups."""
    groups = db.query(ProfitGroup).all()
    return groups

@app.put("/profit-groups/{group_id}/add-product/{product_id}")
def add_product_to_group(group_id: int, product_id: int, db: Session = Depends(get_db)):
    """Add a product to a profit group."""
    group = db.query(ProfitGroup).filter(ProfitGroup.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Profit group not found")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product not in group.products:
        group.products.append(product)
        db.commit()
    
    return {"message": f"Product {product.name} added to group {group.name}"}

@app.put("/profit-groups/{group_id}/remove-product/{product_id}")
def remove_product_from_group(group_id: int, product_id: int, db: Session = Depends(get_db)):
    """Remove a product from a profit group."""
    group = db.query(ProfitGroup).filter(ProfitGroup.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Profit group not found")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product in group.products:
        group.products.remove(product)
        db.commit()
    
    return {"message": f"Product {product.name} removed from group {group.name}"}

# Sale endpoints
@app.post("/sales/")
async def create_sale(customer_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Create a new sale."""
    new_sale = Sale(
        customer_id=customer_id,
        total_amount=0.0  # Will be updated when items are added
    )
    db.add(new_sale)
    db.commit()
    db.refresh(new_sale)
    # Return a dictionary including an empty "items" list.
    return {
        "id": new_sale.id,
        "customer_id": new_sale.customer_id,
        "total_amount": new_sale.total_amount,
        "timestamp": new_sale.timestamp,
        "items": []  # Always include "items"
    }

@app.post("/sales/{sale_id}/add-item")
async def add_item_to_sale(sale_id: int, product_id: int, quantity: int, db: Session = Depends(get_db)):
    """Add an item to a sale."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock_quantity < quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    # Use dynamic pricing
    price_at_sale = product.current_price
    
    # Create sale item
    sale_item = SaleItem(
        sale_id=sale_id,
        product_id=product_id,
        quantity=quantity,
        price_at_sale=price_at_sale
    )
    
    # Update sale total
    sale.total_amount += price_at_sale * quantity
    
    # Update product stock
    product.stock_quantity -= quantity
    
    db.add(sale_item)
    db.commit()
    db.refresh(sale_item)
    
    # Broadcast stock update
    stock_update = json.dumps({
        "product_id": product.id,
        "product_name": product.name,
        "new_stock": product.stock_quantity
    })
    await manager.broadcast(stock_update)
    
    return sale_item

@app.get("/sales/{sale_id}")
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    """Get details of a specific sale."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Get sale items
    items = db.query(SaleItem).filter(SaleItem.sale_id == sale_id).all()
    
    # Format response
    result = {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "total_amount": sale.total_amount,
        "timestamp": sale.timestamp,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": item.price_at_sale,
                "subtotal": item.quantity * item.price_at_sale
            }
            for item in items
        ]
    }
    
    return result

@app.get("/sales/")
def get_sales(start_date: Optional[str] = None, end_date: Optional[str] = None, 
              skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all sales, optionally filtered by date range."""
    query = db.query(Sale)
    
    if start_date:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Sale.timestamp >= start)
    
    if end_date:
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        query = query.filter(Sale.timestamp <= end)
    
    sales = query.order_by(Sale.timestamp.desc()).offset(skip).limit(limit).all()
    
    return sales

# Dynamic pricing endpoints
@app.post("/pricing-rules/")
def create_pricing_rule(product_id: int, rule_type: str, condition: str, 
                        discount_percentage: float, db: Session = Depends(get_db)):
    """Create a new pricing rule."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate rule_type
    valid_types = ['time_of_day', 'day_of_week', 'stock_level', 'line_length', 'vacancy_rate']
    if rule_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid rule type. Must be one of: {', '.join(valid_types)}")
    
    # Validate condition format (should be JSON)
    try:
        json.loads(condition)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Condition must be a valid JSON string")
    
    rule = PricingRule(
        product_id=product_id,
        rule_type=rule_type,
        condition=condition,
        discount_percentage=discount_percentage
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    # Update product's current price
    product.current_price = calculate_dynamic_price(db, product)
    db.commit()
    
    return rule

@app.get("/pricing-rules/")
def get_pricing_rules(product_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all pricing rules, optionally filtered by product."""
    query = db.query(PricingRule)
    
    if product_id:
        query = query.filter(PricingRule.product_id == product_id)
    
    rules = query.all()
    return rules

@app.delete("/pricing-rules/{rule_id}")
def delete_pricing_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a pricing rule."""
    rule = db.query(PricingRule).filter(PricingRule.id == rule_id).first()
    if rule is None:
        raise HTTPException(status_code=404, detail="Pricing rule not found")
    
    product_id = rule.product_id
    db.delete(rule)
    db.commit()
    
    # Update product's current price
    product = db.query(Product).filter(Product.id == product_id).first()
    product.current_price = calculate_dynamic_price(db, product)
    db.commit()
    
    return {"message": "Pricing rule deleted successfully"}

# Store status endpoints
@app.post("/store-status/")
async def update_store_status(vacancy_rate: Optional[float] = None, 
                        line_length: Optional[int] = None, db: Session = Depends(get_db)):
    """Update store status (vacancy rate and line length)."""
    status = StoreStatus(
        vacancy_rate=vacancy_rate if vacancy_rate is not None else 0.0,
        line_length=line_length if line_length is not None else 0
    )
    
    db.add(status)
    db.commit()
    db.refresh(status)
    
    # Update all products' prices based on new store status
    products = db.query(Product).all()
    for product in products:
        product.current_price = calculate_dynamic_price(db, product)
    
    db.commit()
    
    # Broadcast price updates
    price_updates = json.dumps({
        "event": "price_update",
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "current_price": p.current_price
            }
            for p in products
        ]
    })
    await manager.broadcast(price_updates)
    
    return status

@app.get("/store-status/latest")
def get_latest_store_status(db: Session = Depends(get_db)):
    """Get the latest store status."""
    status = db.query(StoreStatus).order_by(StoreStatus.timestamp.desc()).first()
    if status is None:
        return {"vacancy_rate": 0.0, "line_length": 0, "timestamp": datetime.datetime.utcnow()}
    return status

# Prediction endpoints
@app.post("/prediction/train-model")
def train_prediction_model(db: Session = Depends(get_db)):
    """Train the sales prediction model using historical data."""
    global model_trained
    
    # Get all sales data
    sales_data = []
    sale_items = db.query(SaleItem).join(Sale).all()
    
    for item in sale_items:
        sales_data.append({
            'date': item.sale.timestamp,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price_at_sale
        })
    
    if not sales_data:
        raise HTTPException(status_code=400, detail="Not enough sales data to train model")
    
    # Convert to DataFrame
    df = pd.DataFrame(sales_data)
    
    # Train model
    score = prediction_model.train(df)
    model_trained = True
    
    return {"message": "Model trained successfully", "score": score}

def forecast_product_sales(product_id: int, days: int = 7, db: Session = Depends(get_db)):
    """Forecast sales for a specific product."""
    global model_trained
    
    if not model_trained:
        raise HTTPException(status_code=400, detail="Model needs to be trained first")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get historical sales data
    sales_data = []
    sale_items = db.query(SaleItem).join(Sale).filter(SaleItem.product_id == product_id).all()
    
    for item in sale_items:
        sales_data.append({
            'date': item.sale.timestamp,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price_at_sale
        })
    
    if not sales_data:
        raise HTTPException(status_code=400, detail="Not enough sales data for this product")
    
    # Convert to DataFrame
    df = pd.DataFrame(sales_data)
    
    # Make prediction
    forecast = prediction_model.predict_future_sales(
        product_id=product_id,
        days_ahead=days,
        base_price=product.current_price,
        historical_data=df
    )
    
    return forecast.to_dict(orient='records')

@app.get("/prediction/optimal-price/{product_id}")
def get_optimal_price(product_id: int, min_price: Optional[float] = None, 
                     max_price: Optional[float] = None, db: Session = Depends(get_db)):
    """Find the optimal price for a product to maximize profit."""
    global model_trained
    
    if not model_trained:
        raise HTTPException(status_code=400, detail="Model needs to be trained first")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Set price range if not provided
    if min_price is None:
        min_price = product.cost_price * 1.1  # At least 10% above cost
    
    if max_price is None:
        max_price = product.base_price * 1.5  # Up to 50% above base price
    
    # Get historical sales data
    sales_data = []
    sale_items = db.query(SaleItem).join(Sale).filter(SaleItem.product_id == product_id).all()
    
    for item in sale_items:
        sales_data.append({
            'date': item.sale.timestamp,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'price': item.price_at_sale
        })
    
    if not sales_data:
        raise HTTPException(status_code=400, detail="Not enough sales data for this product")
    
    # Convert to DataFrame
    df = pd.DataFrame(sales_data)
    
    # Find optimal price
    optimal_price, predicted_profit = prediction_model.optimize_price(
        product_id=product_id,
        historical_data=df,
        price_range=(min_price, max_price),
        cost_price=product.cost_price
    )
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "cost_price": product.cost_price,
        "current_price": product.current_price,
        "optimal_price": optimal_price,
        "predicted_profit": predicted_profit
    }

# Profit group pricing endpoints
@app.get("/profit-groups/{group_id}/price-check")
def check_profit_group_price(group_id: int, db: Session = Depends(get_db)):
    """Check if a profit group meets its minimum profit criteria."""
    group = db.query(ProfitGroup).filter(ProfitGroup.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Profit group not found")
    
    # Calculate total cost and revenue for the group
    total_cost = sum(product.cost_price for product in group.products)
    total_revenue = sum(product.current_price for product in group.products)
    current_profit = total_revenue - total_cost
    
    # Check if profit meets minimum requirement
    meets_requirement = current_profit >= group.min_profit_price
    
    return {
        "group_id": group.id,
        "group_name": group.name,
        "min_profit_required": group.min_profit_price,
        "current_profit": current_profit,
        "meets_requirement": meets_requirement,
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "cost": p.cost_price,
                "price": p.current_price,
                "individual_profit": p.current_price - p.cost_price
            }
            for p in group.products
        ]
    }

@app.put("/profit-groups/{group_id}/adjust-prices")
def adjust_profit_group_prices(group_id: int, db: Session = Depends(get_db)):
    """Adjust product prices to meet the profit group's minimum profit."""
    group = db.query(ProfitGroup).filter(ProfitGroup.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Profit group not found")
    
    # Calculate current profit
    total_cost = sum(product.cost_price for product in group.products)
    total_revenue = sum(product.current_price for product in group.products)
    current_profit = total_revenue - total_cost
    
    # If profit already meets requirement, no need to adjust
    if current_profit >= group.min_profit_price:
        return {
            "message": "Group already meets profit requirement",
            "current_profit": current_profit,
            "min_profit_required": group.min_profit_price
        }
    
    # Calculate how much more profit is needed
    profit_shortfall = group.min_profit_price - current_profit
    
    # Distribute the shortfall across products
    num_products = len(group.products)
    if num_products == 0:
        return {"message": "No products in this group"}
    
    price_increase_per_product = profit_shortfall / num_products
    
    # Update prices
    for product in group.products:
        product.current_price += price_increase_per_product
        db.commit()
    
    return {
        "message": "Adjusted prices to meet profit requirement",
        "profit_shortfall": profit_shortfall,
        "price_increase_per_product": price_increase_per_product,
        "updated_products": [
            {
                "id": p.id,
                "name": p.name,
                "new_price": p.current_price
            }
            for p in group.products
        ]
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process any client messages if needed
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Analytics endpoints
@app.get("/analytics/sales-summary")
def sales_summary(start_date: Optional[str] = None, end_date: Optional[str] = None, 
                 db: Session = Depends(get_db)):
    """Get summary of sales for a given period."""
    query = db.query(
        func.sum(Sale.total_amount).label("total_revenue"),
        func.count(Sale.id).label("total_sales"),
        func.avg(Sale.total_amount).label("average_sale_value")
    )
    
    if start_date:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(Sale.timestamp >= start)
    
    if end_date:
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        query = query.filter(Sale.timestamp <= end)
    
    result = query.first()
    
    # Calculate profit
    sale_items = db.query(SaleItem).join(Sale).join(Product)
    
    if start_date:
        sale_items = sale_items.filter(Sale.timestamp >= start)
    
    if end_date:
        sale_items = sale_items.filter(Sale.timestamp <= end)
    
    # Calculate profits
    profits = []
    for item in sale_items.all():
        profit = (item.price_at_sale - item.product.cost_price) * item.quantity
        profits.append(profit)
    
    total_profit = sum(profits) if profits else 0
    
    return {
        "total_revenue": result.total_revenue if result.total_revenue else 0,
        "total_profit": total_profit,
        "profit_margin": (total_profit / result.total_revenue * 100) if result.total_revenue else 0,
        "total_sales": result.total_sales,
        "average_sale_value": result.average_sale_value if result.average_sale_value else 0
    }

@app.get("/analytics/top-products")
def top_products(limit: int = 10, db: Session = Depends(get_db)):
    """Get top selling products by quantity."""
    # Join SaleItem with Product and group by product
    query = db.query(
        Product.id,
        Product.name,
        func.sum(SaleItem.quantity).label("total_quantity"),
        func.sum(SaleItem.price_at_sale * SaleItem.quantity).label("total_revenue")
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(limit)
    
    results = query.all()
    
    return [
        {
            "product_id": r.id,
            "product_name": r.name,
            "total_quantity_sold": r.total_quantity,
            "total_revenue": r.total_revenue
        }
        for r in results
    ]

# Utility functions
def calculate_dynamic_price(db, product):
    """Calculate dynamic price based on pricing rules."""
    # Start with base price
    price = product.base_price
    total_discount_percentage = 0
    
    # Get active pricing rules for this product
    rules = db.query(PricingRule).filter(
        PricingRule.product_id == product.id,
        PricingRule.is_active == True
    ).all()
    
    now = datetime.datetime.utcnow()
    
    # Get latest store status
    store_status = db.query(StoreStatus).order_by(StoreStatus.timestamp.desc()).first()
    vacancy_rate = store_status.vacancy_rate if store_status else 0
    line_length = store_status.line_length if store_status else 0
    
    # Apply each rule
    for rule in rules:
        condition = json.loads(rule.condition)
        
        if rule.rule_type == 'time_of_day':
            # Example condition: {"start_hour": 14, "end_hour": 17}
            current_hour = now.hour
            if 'start_hour' in condition and 'end_hour' in condition:
                if condition['start_hour'] <= current_hour < condition['end_hour']:
                    total_discount_percentage += rule.discount_percentage
        
        elif rule.rule_type == 'day_of_week':
            # Example condition: {"days": [0, 6]} (0=Monday, 6=Sunday)
            current_day = now.weekday()
            if 'days' in condition and current_day in condition['days']:
                total_discount_percentage += rule.discount_percentage
        
        elif rule.rule_type == 'stock_level':
            # Example condition: {"min_stock": 10, "max_stock": 50}
            if ('min_stock' in condition and 'max_stock' in condition and 
                condition['min_stock'] <= product.stock_quantity <= condition['max_stock']):
                total_discount_percentage += rule.discount_percentage
        
        elif rule.rule_type == 'line_length':
            # Example condition: {"min_length": 5}
            if 'min_length' in condition and line_length >= condition['min_length']:
                total_discount_percentage += rule.discount_percentage
        
        elif rule.rule_type == 'vacancy_rate':
            # Example condition: {"min_rate": 50}
            if 'min_rate' in condition and vacancy_rate >= condition['min_rate']:
                total_discount_percentage += rule.discount_percentage
    
    # Apply total discount
    if total_discount_percentage > 0:
        price = price * (1 - total_discount_percentage / 100)
    
    # Check profit group constraints
    for group in product.profit_groups:
        group_price_check = check_profit_group_min_price(db, group)
        if not group_price_check["meets_requirement"]:
            # This price would violate the group's minimum profit
            # We'll adjust this product's price to help meet the requirement
            price = adjust_price_for_group(db, product, group, price)
    
    # Ensure price doesn't go below cost
    if price < product.cost_price * 1.05:  # minimum 5% markup
        price = product.cost_price * 1.05
    
    return round(price, 2)

def check_profit_group_min_price(db, group):
    """Check if a group meets its minimum profit requirement."""
    total_cost = sum(product.cost_price for product in group.products)
    total_revenue = sum(product.current_price for product in group.products)
    current_profit = total_revenue - total_cost
    
    return {
        "min_profit_required": group.min_profit_price,
        "current_profit": current_profit,
        "meets_requirement": current_profit >= group.min_profit_price
    }

def adjust_price_for_group(db, product, group, suggested_price):
    """Adjust a product's price to help the group meet its minimum profit requirements."""
    # Calculate current group profit with the suggested price
    total_cost = sum(p.cost_price for p in group.products)
    
    # Calculate what the total revenue would be with this new price
    total_revenue = sum(p.current_price for p in group.products if p.id != product.id) + suggested_price
    
    current_profit = total_revenue - total_cost
    
    # If profit is already sufficient, return the suggested price
    if current_profit >= group.min_profit_price:
        return suggested_price
    
    # Otherwise, calculate how much this product's price needs to increase
    shortfall = group.min_profit_price - current_profit
    
    # Distribute the shortfall across all products in the group
    # For simplicity, we'll just add it to this product's price
    adjusted_price = suggested_price + shortfall
    
    return adjusted_price

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
