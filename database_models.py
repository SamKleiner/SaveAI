from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Association table for many-to-many relationship between products and profit groups
product_group_association = Table(
    'product_group_association', 
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('group_id', Integer, ForeignKey('profit_groups.id'))
)

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    cost_price = Column(Float, nullable=False)
    base_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)  # Current dynamically adjusted price
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    sales = relationship("SaleItem", back_populates="product")
    profit_groups = relationship("ProfitGroup", secondary=product_group_association, back_populates="products")
    pricing_rules = relationship("PricingRule", back_populates="product")
    
    def __repr__(self):
        return f"<Product(name='{self.name}', sku='{self.sku}', price=${self.current_price:.2f})>"


class ProfitGroup(Base):
    __tablename__ = 'profit_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    min_profit_price = Column(Float, nullable=False)  # Minimum profit for the entire group
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    products = relationship("Product", secondary=product_group_association, back_populates="profit_groups")
    
    def __repr__(self):
        return f"<ProfitGroup(name='{self.name}', min_profit=${self.min_profit_price:.2f})>"


class Sale(Base):
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)  # Optional
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sale(id={self.id}, total=${self.total_amount:.2f}, timestamp={self.timestamp})>"


class SaleItem(Base):
    __tablename__ = 'sale_items'
    
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_sale = Column(Float, nullable=False)  # Price when sold (might be discounted)
    
    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sales")
    
    def __repr__(self):
        return f"<SaleItem(product_id={self.product_id}, quantity={self.quantity}, price=${self.price_at_sale:.2f})>"


class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    sales = relationship("Sale", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer(name='{self.name}', email='{self.email}')>"


class PricingRule(Base):
    __tablename__ = 'pricing_rules'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    rule_type = Column(String(50), nullable=False)  # 'time_of_day', 'day_of_week', 'stock_level', etc.
    condition = Column(String(200), nullable=False)  # JSON string with rule conditions
    discount_percentage = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    product = relationship("Product", back_populates="pricing_rules")
    
    def __repr__(self):
        return f"<PricingRule(type='{self.rule_type}', discount={self.discount_percentage}%)>"


class StoreStatus(Base):
    __tablename__ = 'store_status'
    
    id = Column(Integer, primary_key=True)
    vacancy_rate = Column(Float, default=0.0)  # Percentage of capacity
    line_length = Column(Integer, default=0)  # Number of people in line
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<StoreStatus(vacancy_rate={self.vacancy_rate}%, line_length={self.line_length})>"
