from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    stock_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='orders')
    product = relationship('Product', backref='orders')

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', backref='chat_messages')

# Database setup
engine = create_engine('sqlite:///dashboard.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def init_db():
    session = Session()
    try:
        # Create admin user if not exists
        admin = session.query(User).filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            session.add(admin)
            
        # Add sample products
        if session.query(Product).count() == 0:
            products = [
                Product(name='Laptop', description='High-performance laptop', price=999.99, category='Electronics', stock_quantity=50),
                Product(name='Mouse', description='Wireless mouse', price=29.99, category='Electronics', stock_quantity=100),
                Product(name='Keyboard', description='Mechanical keyboard', price=79.99, category='Electronics', stock_quantity=75),
                Product(name='Monitor', description='27-inch 4K monitor', price=399.99, category='Electronics', stock_quantity=30),
            ]
            session.add_all(products)
        
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()