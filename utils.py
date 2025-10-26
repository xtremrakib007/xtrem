import streamlit as st
from database import Session, User, Product, Order, ChatMessage
from datetime import datetime, timedelta
import pandas as pd

def get_session():
    return Session()

def authenticate_user(username, password):
    session = get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None
    finally:
        session.close()

def get_current_user():
    if 'user' in st.session_state:
        return st.session_state.user
    return None

def is_admin():
    user = get_current_user()
    return user and user.role == 'admin'

def get_dashboard_stats():
    session = get_session()
    try:
        total_users = session.query(User).count()
        total_products = session.query(Product).count()
        total_orders = session.query(Order).count()
        pending_orders = session.query(Order).filter_by(status='pending').count()
        
        return {
            'total_users': total_users,
            'total_products': total_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders
        }
    finally:
        session.close()