import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import time
import sqlite3
import hashlib
import json

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    if 'current_chat_user' not in st.session_state:
        st.session_state.current_chat_user = None
    if 'current_chat_room' not in st.session_state:
        st.session_state.current_chat_room = None
    if 'chat_type' not in st.session_state:
        st.session_state.chat_type = 'private'
    if 'last_message_id' not in st.session_state:
        st.session_state.last_message_id = 0
    if 'last_group_message_id' not in st.session_state:
        st.session_state.last_group_message_id = 0
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = True
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = {}
    if 'group_chat_messages' not in st.session_state:
        st.session_state.group_chat_messages = {}

# Database setup
def init_database():
    conn = sqlite3.connect('multi_role_system.db', check_same_thread=False)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            id_number TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            low_stock_alert INTEGER DEFAULT 5,
            description TEXT,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Orders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            date DATE NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_by TEXT NOT NULL
        )
    ''')
    
    # Messages table - Simplified for text only
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user TEXT NOT NULL,
            to_user TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Group messages table - Simplified for text only
    c.execute('''
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user TEXT NOT NULL,
            room_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat rooms table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Room members table
    c.execute('''
        CREATE TABLE IF NOT EXISTS room_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pending approvals table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            data TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pending profile changes table
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_profile_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            phone TEXT,
            id_number TEXT,
            password TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Role upgrade requests table
    c.execute('''
        CREATE TABLE IF NOT EXISTS role_upgrade_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            current_role TEXT NOT NULL,
            requested_role TEXT NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            reviewed_by TEXT,
            reviewed_at TIMESTAMP,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert super admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'xtremrakib'")
    if not c.fetchone():
        super_admin_password = 'Rakib009'
        c.execute('''
            INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('xtremrakib', 'MD RAKIBUL', 'ISLAM', 'rakib@example.com', '0123456789', 'A1234567', super_admin_password, 'superadmin', 'approved'))
    
    # Insert admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        admin_password = 'admin123'
        c.execute('''
            INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'System', 'Administrator', 'admin@example.com', '0000000000', 'ADMIN001', admin_password, 'admin', 'approved'))
    
    # Insert sample products if none exist
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ('Laptop', 'Electronics', 999.99, 15, 'High-performance laptop', 'system'),
            ('Smartphone', 'Electronics', 699.99, 25, 'Latest smartphone model', 'system'),
            ('Desk Chair', 'Furniture', 199.99, 8, 'Ergonomic office chair', 'system')
        ]
        c.executemany('''
            INSERT INTO products (name, category, price, stock, description, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_products)
    
    # Insert sample chat rooms if none exist
    c.execute("SELECT COUNT(*) FROM chat_rooms")
    if c.fetchone()[0] == 0:
        sample_rooms = [
            ('General Chat', 'General discussion for all users', 'system'),
            ('Sales Team', 'Discussion for sales team members', 'system'),
            ('Product Updates', 'Latest product news and updates', 'system')
        ]
        c.executemany('''
            INSERT INTO chat_rooms (name, description, created_by)
            VALUES (?, ?, ?)
        ''', sample_rooms)
        
        # Add superadmin to all rooms
        c.execute("SELECT id FROM chat_rooms")
        room_ids = [row[0] for row in c.fetchall()]
        for room_id in room_ids:
            c.execute('''
                INSERT INTO room_members (room_id, username)
                VALUES (?, ?)
            ''', (room_id, 'xtremrakib'))
            c.execute('''
                INSERT INTO room_members (room_id, username)
                VALUES (?, ?)
            ''', (room_id, 'admin'))
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    return sqlite3.connect('multi_role_system.db', check_same_thread=False)

def execute_query(query, params=(), fetch=False):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        result = c.fetchall()
        conn.close()
        return result
    else:
        conn.commit()
        conn.close()

def execute_query_one(query, params=()):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query, params)
    result = c.fetchone()
    conn.close()
    return result

# Enhanced Role hierarchy with superadmin
role_hierarchy = {
    'superadmin': ['admin', 'manager', 'distributor', 'dealer', 'retailer', 'user'],
    'admin': ['manager', 'distributor', 'dealer', 'retailer', 'user'],
    'manager': ['distributor', 'dealer', 'retailer', 'user'],
    'distributor': ['dealer', 'retailer', 'user'],
    'dealer': ['retailer', 'user'],
    'retailer': ['user']
}

# Approval hierarchy
approval_hierarchy = {
    'user': ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer'],
    'retailer': ['superadmin', 'admin', 'manager', 'distributor', 'dealer'],
    'dealer': ['superadmin', 'admin', 'manager', 'distributor'],
    'distributor': ['superadmin', 'admin', 'manager'],
    'manager': ['superadmin', 'admin'],
    'admin': ['superadmin']
}

# Get users that current user can approve
def get_approvable_users(current_user_role):
    approvable_roles = []
    for role, approvers in approval_hierarchy.items():
        if current_user_role in approvers:
            approvable_roles.append(role)
    return approvable_roles

# Get roles that current user can upgrade users to
def get_upgradable_roles(current_user_role):
    if current_user_role in role_hierarchy:
        return role_hierarchy[current_user_role]
    return []

# Check if user is superadmin
def is_superadmin(user):
    return user and user['role'] == 'superadmin'

# Enhanced Color themes with 3D animations
def apply_theme():
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .main {
            background-color: #1a1a1a;
            color: #f0f0f0;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 50%, #2d2d2d 100%);
        }
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            border: none;
            padding: 12px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
            perspective: 1000px;
        }
        .stButton>button:hover {
            transform: translateY(-3px) rotateX(10deg);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            border-right: 3px solid #667eea;
        }
        .metric-card {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            padding: 20px;
            border-radius: 20px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            transition: all 0.4s ease;
            transform-style: preserve-3d;
        }
        .metric-card:hover {
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 15px 40px rgba(76, 175, 80, 0.3);
        }
        .chat-container {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            border-radius: 25px;
            padding: 25px;
            margin-bottom: 20px;
            max-height: 600px;
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.4);
            border: 2px solid #667eea;
        }
        .chat-message {
            padding: 15px 20px;
            border-radius: 25px;
            margin-bottom: 12px;
            max-width: 75%;
            word-wrap: break-word;
            animation: messageSlide 0.5s ease-out;
            transform-style: preserve-3d;
            transition: all 0.3s ease;
        }
        .chat-message:hover {
            transform: translateY(-2px) rotateY(2deg);
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 8px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .other-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            margin-right: auto;
            border-bottom-left-radius: 8px;
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
        }
        .message-time {
            font-size: 0.7em;
            opacity: 0.8;
            margin-top: 8px;
            text-align: right;
        }
        .message-sender {
            font-weight: bold;
            font-size: 0.8em;
            margin-bottom: 5px;
            opacity: 0.9;
        }
        .approval-item {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            padding: 20px;
            border-radius: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #FFA500;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        .approval-item:hover {
            transform: translateX(5px) rotateY(5deg);
        }
        @keyframes messageSlide {
            from { 
                opacity: 0; 
                transform: translateY(20px) rotateX(45deg);
            }
            to { 
                opacity: 1; 
                transform: translateY(0) rotateX(0);
            }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotateY(0deg); }
            50% { transform: translateY(-10px) rotateY(5deg); }
        }
        .refresh-indicator {
            text-align: center;
            padding: 15px;
            color: #667eea;
            font-size: 0.9em;
            font-weight: bold;
            animation: float 3s ease-in-out infinite;
        }
        .login-container {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            border-radius: 30px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border: 3px solid #667eea;
            transform-style: preserve-3d;
            animation: containerFloat 6s ease-in-out infinite;
        }
        @keyframes containerFloat {
            0%, 100% { transform: translateY(0px) rotateY(0deg); }
            50% { transform: translateY(-15px) rotateY(3deg); }
        }
        .form-input {
            background: rgba(255,255,255,0.1) !important;
            border: 2px solid #667eea !important;
            border-radius: 15px !important;
            color: white !important;
            padding: 12px 15px !important;
            transition: all 0.3s ease !important;
        }
        .form-input:focus {
            background: rgba(255,255,255,0.15) !important;
            border-color: #764ba2 !important;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.5) !important;
            transform: scale(1.02);
        }
        .nav-button {
            transition: all 0.3s ease !important;
            transform-style: preserve-3d !important;
        }
        .nav-button:hover {
            transform: translateX(10px) rotateY(10deg) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        .tab-content {
            background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
            border-radius: 20px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            border: 2px solid #667eea;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .main {
            background-color: #f5f5f5;
            background: linear-gradient(135deg, #e3f2fd 0%, #f5f5f5 50%, #ffffff 100%);
        }
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            border: none;
            padding: 12px 24px;
            font-weight: bold;
            transition: all 0.3s ease;
            transform-style: preserve-3d;
            perspective: 1000px;
        }
        .stButton>button:hover {
            transform: translateY(-3px) rotateX(10deg);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .sidebar .sidebar-content {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-right: 3px solid #667eea;
        }
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 20px;
            border-radius: 20px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: all 0.4s ease;
            transform-style: preserve-3d;
        }
        .metric-card:hover {
            transform: translateY(-5px) rotateY(5deg);
            box-shadow: 0 15px 40px rgba(76, 175, 80, 0.2);
        }
        .chat-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 25px;
            padding: 25px;
            margin-bottom: 20px;
            max-height: 600px;
            overflow-y: auto;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            border: 2px solid #667eea;
        }
        .chat-message {
            padding: 15px 20px;
            border-radius: 25px;
            margin-bottom: 12px;
            max-width: 75%;
            word-wrap: break-word;
            animation: messageSlide 0.5s ease-out;
            transform-style: preserve-3d;
            transition: all 0.3s ease;
        }
        .chat-message:hover {
            transform: translateY(-2px) rotateY(2deg);
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 8px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .other-message {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            margin-right: auto;
            border-bottom-left-radius: 8px;
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
        }
        .message-time {
            font-size: 0.7em;
            opacity: 0.8;
            margin-top: 8px;
            text-align: right;
        }
        .message-sender {
            font-weight: bold;
            font-size: 0.8em;
            margin-bottom: 5px;
            opacity: 0.9;
        }
        .approval-item {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 20px;
            border-radius: 20px;
            margin-bottom: 15px;
            border-left: 5px solid #FFA500;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }
        .approval-item:hover {
            transform: translateX(5px) rotateY(5deg);
        }
        @keyframes messageSlide {
            from { 
                opacity: 0; 
                transform: translateY(20px) rotateX(45deg);
            }
            to { 
                opacity: 1; 
                transform: translateY(0) rotateX(0);
            }
        }
        @keyframes float {
            0%, 100% { transform: translateY(0px) rotateY(0deg); }
            50% { transform: translateY(-10px) rotateY(5deg); }
        }
        .refresh-indicator {
            text-align: center;
            padding: 15px;
            color: #667eea;
            font-size: 0.9em;
            font-weight: bold;
            animation: float 3s ease-in-out infinite;
        }
        .login-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 30px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            border: 3px solid #667eea;
            transform-style: preserve-3d;
            animation: containerFloat 6s ease-in-out infinite;
        }
        @keyframes containerFloat {
            0%, 100% { transform: translateY(0px) rotateY(0deg); }
            50% { transform: translateY(-15px) rotateY(3deg); }
        }
        .form-input {
            background: rgba(255,255,255,0.8) !important;
            border: 2px solid #667eea !important;
            border-radius: 15px !important;
            color: #333 !important;
            padding: 12px 15px !important;
            transition: all 0.3s ease !important;
        }
        .form-input:focus {
            background: rgba(255,255,255,0.9) !important;
            border-color: #764ba2 !important;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
            transform: scale(1.02);
        }
        .nav-button {
            transition: all 0.3s ease !important;
            transform-style: preserve-3d !important;
        }
        .nav-button:hover {
            transform: translateX(10px) rotateY(10deg) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        .tab-content {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border-radius: 20px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            border: 2px solid #667eea;
        }
        </style>
        """, unsafe_allow_html=True)

# Authentication functions
def login_user(username, password, role):
    try:
        user = execute_query_one(
            "SELECT * FROM users WHERE username = ? AND role = ?", 
            (username, role)
        )
        if user:
            # Check if password matches
            if user[7] == password:  # password is at index 7
                # Check if user is approved or is admin/superadmin
                if user[9] == 'approved' or user[8] in ['superadmin', 'admin']:  # status at index 9, role at index 8
                    return {
                        'id': user[0],
                        'username': user[1],
                        'first_name': user[2],
                        'last_name': user[3],
                        'email': user[4],
                        'phone': user[5],
                        'id_number': user[6],
                        'password': user[7],
                        'role': user[8],
                        'status': user[9]
                    }
                else:
                    return None, "Account pending approval"
            else:
                return None, "Incorrect password"
        else:
            return None, "User not found or invalid role"
    except Exception as e:
        return None, f"Login error: {str(e)}"

def signup_user(role, username, first_name, last_name, email, phone, id_number, password):
    try:
        # Check if username exists
        existing_user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
        if existing_user:
            return False, "Username already exists"
        
        # For superadmin/admin, no approval needed
        status = 'approved' if role in ['superadmin', 'admin'] else 'pending'
        
        # Insert user
        execute_query('''
            INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, first_name, last_name, email, phone, id_number, password, role, status))
        
        # Get user ID for pending approval
        user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
        
        # Add to pending approvals if not superadmin/admin
        if role not in ['superadmin', 'admin'] and user:
            approval_data = {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'id_number': id_number,
                'role': role
            }
            
            execute_query('''
                INSERT INTO pending_approvals (user_id, type, data)
                VALUES (?, ?, ?)
            ''', (user[0], 'new_user', json.dumps(approval_data)))
        
        return True, "Registration successful. Waiting for admin approval."
    except Exception as e:
        return False, f"Registration error: {str(e)}"

# Change password function
def change_password(username, current_password, new_password):
    try:
        user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
        if user and user[7] == current_password:
            execute_query('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
            return True, "Password changed successfully"
        else:
            return False, "Current password is incorrect"
    except Exception as e:
        return False, f"Password change error: {str(e)}"

# Role upgrade functions
def request_role_upgrade(username, current_role, requested_role, reason):
    try:
        # Check if there's already a pending request
        existing_request = execute_query_one(
            "SELECT * FROM role_upgrade_requests WHERE username = ? AND status = 'pending'",
            (username,)
        )
        if existing_request:
            return False, "You already have a pending role upgrade request"
        
        execute_query('''
            INSERT INTO role_upgrade_requests (username, current_role, requested_role, reason)
            VALUES (?, ?, ?, ?)
        ''', (username, current_role, requested_role, reason))
        
        return True, "Role upgrade request submitted successfully"
    except Exception as e:
        return False, f"Role upgrade request error: {str(e)}"

def get_pending_role_upgrades(approver_role):
    try:
        # Get roles that the approver can approve upgrades for
        approvable_roles = []
        for role, approvers in approval_hierarchy.items():
            if approver_role in approvers:
                approvable_roles.append(role)
        
        if not approvable_roles:
            return []
        
        return execute_query('''
            SELECT rur.*, u.first_name, u.last_name 
            FROM role_upgrade_requests rur
            JOIN users u ON rur.username = u.username
            WHERE rur.status = 'pending' AND rur.current_role IN ({})
        '''.format(','.join(['?'] * len(approvable_roles))), approvable_roles, fetch=True)
    except Exception as e:
        st.error(f"Error getting pending upgrades: {str(e)}")
        return []

def approve_role_upgrade(request_id, approver_username):
    try:
        request = execute_query_one("SELECT * FROM role_upgrade_requests WHERE id = ?", (request_id,))
        if request:
            # Update user role
            execute_query('UPDATE users SET role = ? WHERE username = ?', (request[3], request[1]))
            # Update request status
            execute_query('''
                UPDATE role_upgrade_requests 
                SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (approver_username, request_id))
            return True, "Role upgraded successfully"
        return False, "Request not found"
    except Exception as e:
        return False, f"Approval error: {str(e)}"

def reject_role_upgrade(request_id, approver_username):
    try:
        execute_query('''
            UPDATE role_upgrade_requests 
            SET status = 'rejected', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (approver_username, request_id))
        return True, "Role upgrade request rejected"
    except Exception as e:
        return False, f"Rejection error: {str(e)}"

# Page navigation
def navigate_to(page):
    st.session_state.current_page = page

# UI Components with 3D effects
def render_header():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("<h1 style='color: #4CAF50; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>Multi-Role Authentication System</h1>", unsafe_allow_html=True)
    with col2:
        if st.session_state.authenticated:
            role_display = "👑 " + st.session_state.current_user['role'].title() if st.session_state.current_user['role'] == 'superadmin' else st.session_state.current_user['role'].title()
            st.write(f"👋 Welcome, **{st.session_state.current_user['first_name']}**")
            st.write(f"Role: **{role_display}**")
    with col3:
        if st.session_state.authenticated:
            if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.current_page = 'login'
                st.rerun()
        # Theme toggle
        if st.button("🌙" if st.session_state.theme == 'light' else "☀️", use_container_width=True, key="theme_btn"):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()

def render_sidebar():
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown("<h2 style='color: #4CAF50; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);'>Navigation</h2>", unsafe_allow_html=True)
            
            # Dashboard
            if st.button("🏠 Dashboard", use_container_width=True, key="dashboard_btn"):
                navigate_to('dashboard')
            
            # Profile
            if st.button("👤 Profile", use_container_width=True, key="profile_btn"):
                navigate_to('profile')
            
            # User Management
            if st.session_state.current_user['role'] in role_hierarchy:
                if st.button("👥 User Management", use_container_width=True, key="user_mgmt_btn"):
                    navigate_to('user_management')
            
            # Products, Orders, Stock, Reports (for business roles)
            if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
                if st.button("📦 Products", use_container_width=True, key="products_btn"):
                    navigate_to('products')
                if st.button("🛒 Orders", use_container_width=True, key="orders_btn"):
                    navigate_to('orders')
                if st.button("📊 Stock", use_container_width=True, key="stock_btn"):
                    navigate_to('stock')
                if st.button("📈 Reports", use_container_width=True, key="reports_btn"):
                    navigate_to('reports')
            
            # Chat and Settings for all authenticated users
            if st.button("💬 Chat", use_container_width=True, key="chat_btn"):
                navigate_to('chat')
            if st.button("⚙️ Settings", use_container_width=True, key="settings_btn"):
                navigate_to('settings')
            
            # Approvals for roles that can approve
            if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
                # Check if there are pending approvals
                approvable_roles = get_approvable_users(st.session_state.current_user['role'])
                pending_users_count = execute_query_one(
                    "SELECT COUNT(*) FROM users WHERE status = 'pending' AND role IN ({})".format(
                        ','.join(['?'] * len(approvable_roles))
                    ), approvable_roles
                )[0] if approvable_roles else 0
                
                pending_changes_count = execute_query_one("SELECT COUNT(*) FROM pending_profile_changes")[0] or 0
                
                pending_upgrades_count = execute_query_one("SELECT COUNT(*) FROM role_upgrade_requests WHERE status = 'pending'")[0] or 0
                
                total_pending = pending_users_count + pending_changes_count + pending_upgrades_count
                
                approval_text = f"✅ Approvals ({total_pending})" if total_pending > 0 else "✅ Approvals"
                if st.button(approval_text, use_container_width=True, key="approvals_btn"):
                    navigate_to('approvals')

# Fixed Login Page with 3D effects
def render_login():
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4CAF50; margin-bottom: 30px;'>🔐 Login</h1>", unsafe_allow_html=True)
    
    with st.form("login_form", border=False):
        role = st.selectbox("👤 Role", ["superadmin", "admin", "manager", "distributor", "dealer", "retailer", "user"])
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        
        submit = st.form_submit_button("🚀 Login", use_container_width=True)
        
        if submit:
            result = login_user(username, password, role)
            if isinstance(result, tuple):
                # Error case
                st.error(result[1])
            else:
                # Success case
                user = result
                if user:
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    st.session_state.current_page = 'dashboard'
                    st.success("🎉 Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials or account pending approval")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("Don't have an account?")
    if st.button("📝 Sign Up", use_container_width=True, key="signup_btn"):
        navigate_to('signup')

def render_signup():
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #4CAF50; margin-bottom: 30px;'>📝 Sign Up</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form", border=False):
        role = st.selectbox("👤 Role", ["manager", "distributor", "dealer", "retailer", "user"])
        username = st.text_input("👤 Username")
        first_name = st.text_input("👤 First Name")
        last_name = st.text_input("👤 Last Name")
        email = st.text_input("📧 Email")
        phone = st.text_input("📱 Phone")
        id_number = st.text_input("🆔 ID Number")
        password = st.text_input("🔒 Password", type="password")
        
        submit = st.form_submit_button("🚀 Sign Up", use_container_width=True)
        
        if submit:
            success, message = signup_user(role, username, first_name, last_name, email, phone, id_number, password)
            if success:
                st.success(f"🎉 {message}")
                navigate_to('login')
            else:
                st.error(f"❌ {message}")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.write("Already have an account?")
    if st.button("🔐 Login", use_container_width=True, key="login_btn"):
        navigate_to('login')

# Dashboard
def render_dashboard():
    st.header("📊 Dashboard")
    
    # Special badge for superadmin with 3D effect
    if is_superadmin(st.session_state.current_user):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); 
                    padding: 20px; border-radius: 20px; text-align: center; 
                    box-shadow: 0 10px 30px rgba(255,215,0,0.3);
                    animation: float 4s ease-in-out infinite;
                    border: 3px solid #FFD700;">
            <h2 style="color: #000; margin: 0;">👑 SUPER ADMIN MODE</h2>
            <p style="color: #000; margin: 0;">Full system access granted!</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
    
    st.write(f"Welcome, **{st.session_state.current_user['first_name']} {st.session_state.current_user['last_name']}**!")
    
    role_display = "👑 " + st.session_state.current_user['role'].title() if st.session_state.current_user['role'] == 'superadmin' else st.session_state.current_user['role'].title()
    st.write(f"Role: **{role_display}**")
    
    # Display quick stats based on role with 3D cards
    if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_products = execute_query_one("SELECT COUNT(*) FROM products")[0] or 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>📦 Total Products</h3>
                <h2 style="color: #4CAF50;">{total_products}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_orders = execute_query_one("SELECT COUNT(*) FROM orders")[0] or 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>🛒 Total Orders</h3>
                <h2 style="color: #2196F3;">{total_orders}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_sales = execute_query_one("SELECT COALESCE(SUM(total), 0) FROM orders")[0] or 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>💰 Total Sales</h3>
                <h2 style="color: #FF9800;">${total_sales:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_users = execute_query_one("SELECT COUNT(*) FROM users")[0] or 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>👥 Total Users</h3>
                <h2 style="color: #9C27B0;">{total_users}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick actions based on role with 3D buttons
    st.subheader("🚀 Quick Actions")
    cols = st.columns(3)
    
    if st.session_state.current_user['role'] in role_hierarchy:
        with cols[0]:
            if st.button("👥 User Management", use_container_width=True, key="quick_user_mgmt"):
                navigate_to('user_management')
    
    if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        with cols[1]:
            if st.button("📦 Add Product", use_container_width=True, key="quick_products"):
                navigate_to('products')
        with cols[2]:
            if st.button("🛒 Create Order", use_container_width=True, key="quick_orders"):
                navigate_to('orders')
    
    # Show pending approvals notification for admins and managers
    if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        approvable_roles = get_approvable_users(st.session_state.current_user['role'])
        if approvable_roles:
            pending_users_count = execute_query_one(
                "SELECT COUNT(*) FROM users WHERE status = 'pending' AND role IN ({})".format(
                    ','.join(['?'] * len(approvable_roles))
                ), approvable_roles
            )[0] if approvable_roles else 0
            
            pending_changes_count = execute_query_one("SELECT COUNT(*) FROM pending_profile_changes")[0] or 0
            
            pending_upgrades_count = execute_query_one("SELECT COUNT(*) FROM role_upgrade_requests WHERE status = 'pending'")[0] or 0
            
            total_pending = pending_users_count + pending_changes_count + pending_upgrades_count
            
            if total_pending > 0:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); 
                            padding: 15px; border-radius: 15px; text-align: center;
                            box-shadow: 0 5px 15px rgba(255,152,0,0.3);
                            animation: pulse 2s infinite;">
                    <h4 style="color: white; margin: 0;">🔔 You have {total_pending} pending approval(s)!</h4>
                    <p style="color: white; margin: 0;">Click on 'Approvals' in the sidebar to review them.</p>
                </div>
                """, unsafe_allow_html=True)

# Profile Page
def render_profile():
    st.header("👤 Profile Management")
    
    user = st.session_state.current_user
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", value=user['first_name'])
            last_name = st.text_input("Last Name", value=user['last_name'])
            email = st.text_input("Email", value=user['email'])
        
        with col2:
            phone = st.text_input("Phone", value=user['phone'])
            id_number = st.text_input("ID Number", value=user['id_number'])
            username = st.text_input("Username", value=user['username'], disabled=True)
        
        submit = st.form_submit_button("💾 Update Profile")
        
        if submit:
            # Check if any changes were made
            if (first_name != user['first_name'] or last_name != user['last_name'] or 
                email != user['email'] or phone != user['phone'] or id_number != user['id_number']):
                
                # Store changes in pending_profile_changes table
                execute_query('''
                    INSERT INTO pending_profile_changes (username, first_name, last_name, email, phone, id_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (username, first_name, last_name, email, phone, id_number))
                
                st.success("✅ Profile changes submitted for approval!")
            else:
                st.info("ℹ️ No changes detected")
    
    # Password change section
    st.subheader("🔒 Change Password")
    with st.form("password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submit = st.form_submit_button("🔄 Change Password")
        
        if submit:
            if new_password == confirm_password:
                success, message = change_password(user['username'], current_password, new_password)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
            else:
                st.error("❌ New passwords do not match!")
    
    # Role upgrade request section
    if user['role'] != 'superadmin' and user['role'] != 'admin':
        st.subheader("📈 Request Role Upgrade")
        upgradable_roles = get_upgradable_roles(user['role'])
        if upgradable_roles:
            with st.form("role_upgrade_form"):
                requested_role = st.selectbox("Requested Role", upgradable_roles)
                reason = st.text_area("Reason for Upgrade")
                
                submit = st.form_submit_button("🚀 Request Upgrade")
                
                if submit:
                    success, message = request_role_upgrade(user['username'], user['role'], requested_role, reason)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        else:
            st.info("ℹ️ You are at the highest role available for your account.")

# User Management Page
def render_user_management():
    st.header("👥 User Management")
    
    user = st.session_state.current_user
    
    if user['role'] not in role_hierarchy:
        st.error("❌ You don't have permission to access user management.")
        return
    
    # Create new user section
    st.subheader("➕ Create New User")
    with st.form("create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_role = st.selectbox("Role", get_upgradable_roles(user['role']))
            new_username = st.text_input("Username")
            new_first_name = st.text_input("First Name")
            new_last_name = st.text_input("Last Name")
        
        with col2:
            new_email = st.text_input("Email")
            new_phone = st.text_input("Phone")
            new_id_number = st.text_input("ID Number")
            new_password = st.text_input("Password", type="password")
        
        submit = st.form_submit_button("👤 Create User")
        
        if submit:
            success, message = signup_user(new_role, new_username, new_first_name, new_last_name, 
                                         new_email, new_phone, new_id_number, new_password)
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
    
    # View and manage users section
    st.subheader("📋 User List")
    
    # Get users that current user can manage
    manageable_roles = get_upgradable_roles(user['role'])
    if manageable_roles:
        users = execute_query(
            "SELECT * FROM users WHERE role IN ({})".format(','.join(['?'] * len(manageable_roles))),
            manageable_roles, fetch=True
        )
        
        if users:
            user_data = []
            for u in users:
                user_data.append({
                    'ID': u[0],
                    'Username': u[1],
                    'First Name': u[2],
                    'Last Name': u[3],
                    'Email': u[4],
                    'Phone': u[5],
                    'Role': u[8],
                    'Status': u[9]
                })
            
            df = pd.DataFrame(user_data)
            st.dataframe(df, use_container_width=True)
            
            # User actions
            st.subheader("🛠️ User Actions")
            selected_username = st.selectbox("Select User", [u[1] for u in users])
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Update Role", use_container_width=True, key="update_role_btn"):
                    st.session_state.selected_user_for_role = selected_username
                    st.rerun()
            
            with col2:
                if st.button("✅ Approve User", use_container_width=True, key="approve_user_btn"):
                    execute_query("UPDATE users SET status = 'approved' WHERE username = ?", (selected_username,))
                    st.success(f"✅ User {selected_username} approved successfully!")
                    st.rerun()
            
            with col3:
                if st.button("❌ Delete User", use_container_width=True, key="delete_user_btn"):
                    execute_query("DELETE FROM users WHERE username = ?", (selected_username,))
                    st.success(f"✅ User {selected_username} deleted successfully!")
                    st.rerun()
            
            # Role update section
            if hasattr(st.session_state, 'selected_user_for_role'):
                st.subheader(f"🔄 Update Role for {st.session_state.selected_user_for_role}")
                current_user_role = execute_query_one(
                    "SELECT role FROM users WHERE username = ?", 
                    (st.session_state.selected_user_for_role,)
                )[0]
                
                new_role = st.selectbox("New Role", get_upgradable_roles(user['role']), key="new_role_select")
                if st.button("💾 Update Role", key="confirm_role_update"):
                    execute_query(
                        "UPDATE users SET role = ? WHERE username = ?", 
                        (new_role, st.session_state.selected_user_for_role)
                    )
                    st.success(f"✅ Role updated from {current_user_role} to {new_role}!")
                    del st.session_state.selected_user_for_role
                    st.rerun()
        else:
            st.info("ℹ️ No users found for your management level.")
    else:
        st.info("ℹ️ You cannot manage any users at your current role level.")

# Products Page
def render_products():
    st.header("📦 Product Management")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        st.error("❌ You don't have permission to access product management.")
        return
    
    # Add new product
    st.subheader("➕ Add New Product")
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Product Name")
            category = st.selectbox("Category", ["Electronics", "Furniture", "Clothing", "Food", "Other"])
            price = st.number_input("Price", min_value=0.0, step=0.01)
        
        with col2:
            stock = st.number_input("Stock Quantity", min_value=0, step=1)
            low_stock_alert = st.number_input("Low Stock Alert", min_value=1, value=5, step=1)
            description = st.text_area("Description")
        
        submit = st.form_submit_button("📦 Add Product")
        
        if submit:
            execute_query('''
                INSERT INTO products (name, category, price, stock, low_stock_alert, description, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, category, price, stock, low_stock_alert, description, user['username']))
            st.success("✅ Product added successfully!")
            st.rerun()
    
    # View and manage products
    st.subheader("📋 Product List")
    products = execute_query("SELECT * FROM products", fetch=True)
    
    if products:
        product_data = []
        for p in products:
            product_data.append({
                'ID': p[0],
                'Name': p[1],
                'Category': p[2],
                'Price': f"${p[3]:.2f}",
                'Stock': p[4],
                'Low Stock Alert': p[5],
                'Description': p[6]
            })
        
        df = pd.DataFrame(product_data)
        st.dataframe(df, use_container_width=True)
        
        # Product actions
        st.subheader("🛠️ Product Actions")
        selected_product_id = st.selectbox("Select Product", [p[0] for p in products], format_func=lambda x: f"ID: {x} - {next(p[1] for p in products if p[0] == x)}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✏️ Edit Product", use_container_width=True, key="edit_product_btn"):
                st.session_state.editing_product = selected_product_id
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete Product", use_container_width=True, key="delete_product_btn"):
                execute_query("DELETE FROM products WHERE id = ?", (selected_product_id,))
                st.success("✅ Product deleted successfully!")
                st.rerun()
        
        # Edit product section
        if hasattr(st.session_state, 'editing_product'):
            product = execute_query_one("SELECT * FROM products WHERE id = ?", (st.session_state.editing_product,))
            if product:
                st.subheader(f"✏️ Edit Product: {product[1]}")
                with st.form("edit_product_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("Product Name", value=product[1])
                        edit_category = st.selectbox("Category", ["Electronics", "Furniture", "Clothing", "Food", "Other"], 
                                                   index=["Electronics", "Furniture", "Clothing", "Food", "Other"].index(product[2]))
                        edit_price = st.number_input("Price", value=float(product[3]), min_value=0.0, step=0.01)
                    
                    with col2:
                        edit_stock = st.number_input("Stock Quantity", value=product[4], min_value=0, step=1)
                        edit_low_stock_alert = st.number_input("Low Stock Alert", value=product[5], min_value=1, step=1)
                        edit_description = st.text_area("Description", value=product[6] or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Save Changes"):
                            execute_query('''
                                UPDATE products 
                                SET name = ?, category = ?, price = ?, stock = ?, low_stock_alert = ?, description = ?
                                WHERE id = ?
                            ''', (edit_name, edit_category, edit_price, edit_stock, edit_low_stock_alert, edit_description, st.session_state.editing_product))
                            st.success("✅ Product updated successfully!")
                            del st.session_state.editing_product
                            st.rerun()
                    
                    with col2:
                        if st.form_submit_button("❌ Cancel"):
                            del st.session_state.editing_product
                            st.rerun()
    else:
        st.info("ℹ️ No products found. Add your first product above!")

# Orders Page
def render_orders():
    st.header("🛒 Order Management")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        st.error("❌ You don't have permission to access order management.")
        return
    
    # Create new order
    st.subheader("➕ Create New Order")
    with st.form("create_order_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer = st.text_input("Customer Name")
            products = execute_query("SELECT id, name, price, stock FROM products", fetch=True)
            product_options = {f"{p[1]} (${p[2]:.2f})": p[0] for p in products}
            selected_product = st.selectbox("Product", list(product_options.keys()))
            product_id = product_options[selected_product]
            product_name = selected_product.split(" (")[0]
        
        with col2:
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
            selected_product_data = next(p for p in products if p[0] == product_id)
            unit_price = selected_product_data[2]
            total = quantity * unit_price
            order_date = st.date_input("Order Date", value=date.today())
            notes = st.text_area("Notes")
        
        st.write(f"**Unit Price:** ${unit_price:.2f}")
        st.write(f"**Total:** ${total:.2f}")
        
        submit = st.form_submit_button("🛒 Create Order")
        
        if submit:
            # Check stock availability
            if selected_product_data[3] < quantity:
                st.error(f"❌ Insufficient stock! Available: {selected_product_data[3]}")
            else:
                # Create order
                execute_query('''
                    INSERT INTO orders (customer, product_id, product_name, quantity, unit_price, total, date, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (customer, product_id, product_name, quantity, unit_price, total, order_date, notes, user['username']))
                
                # Update product stock
                new_stock = selected_product_data[3] - quantity
                execute_query('''
                    UPDATE products SET stock = ? WHERE id = ?
                ''', (new_stock, product_id))
                
                st.success("✅ Order created successfully!")
                st.rerun()
    
    # View and manage orders
    st.subheader("📋 Order List")
    orders = execute_query("SELECT * FROM orders", fetch=True)
    
    if orders:
        order_data = []
        for o in orders:
            order_data.append({
                'ID': o[0],
                'Customer': o[1],
                'Product': o[3],
                'Quantity': o[4],
                'Unit Price': f"${o[5]:.2f}",
                'Total': f"${o[6]:.2f}",
                'Date': o[7],
                'Status': o[8],
                'Created By': o[10]
            })
        
        df = pd.DataFrame(order_data)
        st.dataframe(df, use_container_width=True)
        
        # Order actions
        st.subheader("🛠️ Order Actions")
        selected_order_id = st.selectbox("Select Order", [o[0] for o in orders], format_func=lambda x: f"Order #{x}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_status = st.selectbox("Update Status", ["pending", "processing", "completed", "cancelled"])
            if st.button("🔄 Update Status", use_container_width=True, key="update_status_btn"):
                execute_query("UPDATE orders SET status = ? WHERE id = ?", (new_status, selected_order_id))
                st.success("✅ Order status updated successfully!")
                st.rerun()
        
        with col2:
            if st.button("🗑️ Delete Order", use_container_width=True, key="delete_order_btn"):
                # Restore product stock before deleting
                order = execute_query_one("SELECT product_id, quantity FROM orders WHERE id = ?", (selected_order_id,))
                if order:
                    product = execute_query_one("SELECT stock FROM products WHERE id = ?", (order[0],))
                    if product:
                        new_stock = product[0] + order[1]
                        execute_query("UPDATE products SET stock = ? WHERE id = ?", (new_stock, order[0]))
                
                execute_query("DELETE FROM orders WHERE id = ?", (selected_order_id,))
                st.success("✅ Order deleted successfully!")
                st.rerun()
    else:
        st.info("ℹ️ No orders found. Create your first order above!")

# Stock Page
def render_stock():
    st.header("📊 Stock Management")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        st.error("❌ You don't have permission to access stock management.")
        return
    
    # Stock overview
    st.subheader("📈 Stock Overview")
    products = execute_query("SELECT * FROM products", fetch=True)
    
    if products:
        # Low stock alert
        low_stock_products = [p for p in products if p[4] <= p[5]]
        if low_stock_products:
            st.warning(f"🚨 {len(low_stock_products)} product(s) are low on stock!")
            for product in low_stock_products:
                st.error(f"**{product[1]}** - Stock: {product[4]}, Alert Level: {product[5]}")
        
        # Stock metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_products = len(products)
            st.metric("Total Products", total_products)
        
        with col2:
            total_stock_value = sum(p[3] * p[4] for p in products)
            st.metric("Total Stock Value", f"${total_stock_value:.2f}")
        
        with col3:
            out_of_stock = len([p for p in products if p[4] == 0])
            st.metric("Out of Stock", out_of_stock)
        
        # Stock table
        st.subheader("📋 Stock Details")
        stock_data = []
        for p in products:
            status = "🟢 Good" if p[4] > p[5] else "🟡 Low" if p[4] > 0 else "🔴 Out"
            stock_data.append({
                'ID': p[0],
                'Name': p[1],
                'Category': p[2],
                'Price': f"${p[3]:.2f}",
                'Stock': p[4],
                'Alert Level': p[5],
                'Status': status
            })
        
        df = pd.DataFrame(stock_data)
        st.dataframe(df, use_container_width=True)
        
        # Stock update section
        st.subheader("🔄 Update Stock")
        selected_product_id = st.selectbox("Select Product", [p[0] for p in products], format_func=lambda x: f"{next(p[1] for p in products if p[0] == x)} (Current: {next(p[4] for p in products if p[0] == x)})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_stock = st.number_input("New Stock Quantity", min_value=0, value=next(p[4] for p in products if p[0] == selected_product_id), step=1)
        
        with col2:
            new_alert_level = st.number_input("New Alert Level", min_value=1, value=next(p[5] for p in products if p[0] == selected_product_id), step=1)
        
        if st.button("💾 Update Stock", use_container_width=True, key="update_stock_btn"):
            execute_query('''
                UPDATE products 
                SET stock = ?, low_stock_alert = ?
                WHERE id = ?
            ''', (new_stock, new_alert_level, selected_product_id))
            st.success("✅ Stock updated successfully!")
            st.rerun()
    else:
        st.info("ℹ️ No products found. Add products first in the Products section.")

# Reports Page
def render_reports():
    st.header("📈 Reports & Analytics")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        st.error("❌ You don't have permission to access reports.")
        return
    
    # Sales report
    st.subheader("💰 Sales Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", value=date.today().replace(day=1))
    
    with col2:
        end_date = st.date_input("End Date", value=date.today())
    
    if st.button("📊 Generate Report", use_container_width=True, key="generate_report_btn"):
        # Sales summary
        total_sales = execute_query_one(
            "SELECT COALESCE(SUM(total), 0) FROM orders WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        )[0] or 0
        
        total_orders = execute_query_one(
            "SELECT COUNT(*) FROM orders WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        )[0] or 0
        
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Sales", f"${total_sales:.2f}")
        
        with col2:
            st.metric("Total Orders", total_orders)
        
        with col3:
            st.metric("Average Order Value", f"${avg_order_value:.2f}")
        
        # Top products
        st.subheader("🏆 Top Products")
        top_products = execute_query('''
            SELECT product_name, SUM(quantity) as total_quantity, SUM(total) as total_revenue
            FROM orders 
            WHERE date BETWEEN ? AND ?
            GROUP BY product_name 
            ORDER BY total_revenue DESC 
            LIMIT 5
        ''', (start_date, end_date), fetch=True)
        
        if top_products:
            product_data = []
            for p in top_products:
                product_data.append({
                    'Product': p[0],
                    'Quantity Sold': p[1],
                    'Revenue': f"${p[2]:.2f}"
                })
            
            df_products = pd.DataFrame(product_data)
            st.dataframe(df_products, use_container_width=True)
        else:
            st.info("ℹ️ No sales data for the selected period.")
    
    # Inventory report
    st.subheader("📦 Inventory Report")
    
    products = execute_query("SELECT * FROM products", fetch=True)
    if products:
        inventory_data = []
        for p in products:
            status = "🟢 Good" if p[4] > p[5] else "🟡 Low" if p[4] > 0 else "🔴 Out"
            value = p[3] * p[4]
            inventory_data.append({
                'Product': p[1],
                'Category': p[2],
                'Stock': p[4],
                'Alert Level': p[5],
                'Status': status,
                'Value': f"${value:.2f}"
            })
        
        df_inventory = pd.DataFrame(inventory_data)
        st.dataframe(df_inventory, use_container_width=True)
        
        # Export options
        st.subheader("📤 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Export Sales Data", use_container_width=True, key="export_sales_btn"):
                orders_data = execute_query("SELECT * FROM orders", fetch=True)
                if orders_data:
                    orders_df = pd.DataFrame(orders_data, columns=['ID', 'Customer', 'Product ID', 'Product Name', 'Quantity', 'Unit Price', 'Total', 'Date', 'Status', 'Notes', 'Created By'])
                    st.download_button(
                        label="📥 Download Sales CSV",
                        data=orders_df.to_csv(index=False),
                        file_name=f"sales_data_{date.today()}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("📥 Export Inventory Data", use_container_width=True, key="export_inventory_btn"):
                inventory_df = pd.DataFrame(inventory_data)
                st.download_button(
                    label="📥 Download Inventory CSV",
                    data=inventory_df.to_csv(index=False),
                    file_name=f"inventory_data_{date.today()}.csv",
                    mime="text/csv"
                )

# Enhanced Chat functions with real-time refresh
def get_chat_rooms():
    return execute_query('''
        SELECT cr.* FROM chat_rooms cr
        JOIN room_members rm ON cr.id = rm.room_id
        WHERE rm.username = ?
        ORDER BY cr.name
    ''', (st.session_state.current_user['username'],), fetch=True)

def get_room_members(room_id):
    return execute_query('''
        SELECT username FROM room_members 
        WHERE room_id = ?
    ''', (room_id,), fetch=True)

def is_room_member(room_id):
    result = execute_query_one(
        "SELECT * FROM room_members WHERE room_id = ? AND username = ?",
        (room_id, st.session_state.current_user['username'])
    )
    return result is not None

def add_user_to_room(room_id, username):
    if not execute_query_one(
        "SELECT * FROM room_members WHERE room_id = ? AND username = ?",
        (room_id, username)
    ):
        execute_query(
            "INSERT INTO room_members (room_id, username) VALUES (?, ?)",
            (room_id, username)
        )

def get_private_messages(user1, user2):
    return execute_query('''
        SELECT * FROM messages 
        WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
        ORDER BY timestamp ASC
    ''', (user1, user2, user2, user1), fetch=True)

def get_group_messages(room_id):
    return execute_query('''
        SELECT * FROM group_messages 
        WHERE room_id = ?
        ORDER BY timestamp ASC
    ''', (room_id,), fetch=True)

def send_private_message(from_user, to_user, text):
    execute_query('''
        INSERT INTO messages (from_user, to_user, text)
        VALUES (?, ?, ?)
    ''', (from_user, to_user, text))

def send_group_message(from_user, room_id, text):
    execute_query('''
        INSERT INTO group_messages (from_user, room_id, text)
        VALUES (?, ?, ?)
    ''', (from_user, room_id, text))

# Check for new messages with improved performance
def check_new_messages():
    current_user = st.session_state.current_user['username']
    
    if st.session_state.chat_type == 'private' and st.session_state.current_chat_user:
        # Check for new private messages
        latest_message = execute_query_one(
            "SELECT MAX(id) FROM messages WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)",
            (current_user, st.session_state.current_chat_user, st.session_state.current_chat_user, current_user)
        )
        current_max_id = latest_message[0] if latest_message and latest_message[0] else 0
        
        if current_max_id != st.session_state.last_message_id:
            st.session_state.last_message_id = current_max_id
            # Clear cached messages to force refresh
            cache_key = f"{current_user}_{st.session_state.current_chat_user}"
            if cache_key in st.session_state.chat_messages:
                del st.session_state.chat_messages[cache_key]
            return True
            
    elif st.session_state.chat_type == 'group' and st.session_state.current_chat_room:
        # Check for new group messages
        latest_message = execute_query_one(
            "SELECT MAX(id) FROM group_messages WHERE room_id = ?",
            (st.session_state.current_chat_room,)
        )
        current_max_id = latest_message[0] if latest_message and latest_message[0] else 0
        
        if current_max_id != st.session_state.last_group_message_id:
            st.session_state.last_group_message_id = current_max_id
            # Clear cached messages to force refresh
            cache_key = f"room_{st.session_state.current_chat_room}"
            if cache_key in st.session_state.group_chat_messages:
                del st.session_state.group_chat_messages[cache_key]
            return True
    
    return False

def get_unread_private_count(current_user, other_user):
    """Get count of unread messages from a specific user"""
    last_read = st.session_state.last_message_id
    result = execute_query_one(
        "SELECT COUNT(*) FROM messages WHERE ((from_user = ? AND to_user = ?) AND id > ?)",
        (other_user, current_user, last_read)
    )
    return result[0] if result else 0

def get_unread_group_count(room_id, username):
    """Get count of unread messages in a group"""
    last_read = st.session_state.last_group_message_id
    result = execute_query_one(
        "SELECT COUNT(*) FROM group_messages WHERE room_id = ? AND id > ? AND from_user != ?",
        (room_id, last_read, username)
    )
    return result[0] if result else 0

def get_recent_private_chats(username):
    """Get recent private conversations"""
    return execute_query('''
        SELECT from_user, to_user, MAX(timestamp) as last_time
        FROM messages 
        WHERE from_user = ? OR to_user = ?
        GROUP BY 
            CASE WHEN from_user = ? THEN to_user ELSE from_user END
        ORDER BY last_time DESC
    ''', (username, username, username), fetch=True)

def get_room_member_count(room_id):
    """Get number of members in a room"""
    result = execute_query_one("SELECT COUNT(*) FROM room_members WHERE room_id = ?", (room_id,))
    return result[0] if result else 0

def display_message(message):
    """Display a single private message with proper formatting"""
    try:
        # Add validation at the start of the function
        if not message or len(message) < 2:
            return  # Skip invalid messages
        
        # Safely extract timestamp - fix for the IndexError
        timestamp = ''
        if message[1]:
            try:
                # Original problematic code: message[1].split('')[1][15]
                # Safe extraction based on your message format
                parts = message[1].split(' ')
                if len(parts) > 1 and len(parts[1]) > 15:
                    timestamp = parts[1][15]
                else:
                    timestamp = ''
            except (IndexError, AttributeError) as e:
                timestamp = ''
        
        # Display logic based on message sender
        if message[1] == st.session_state.current_user['username']:
            # User's message (right side)
            st.markdown(f"""
            <div class="chat-message user-message">
                <div>{message[3]}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Other user's message (left side)
            user_details = execute_query_one("SELECT first_name, last_name FROM users WHERE username = ?", (message[1],))
            sender_name = f"{user_details[0]} {user_details[1]}" if user_details else message[1]
            
            st.markdown(f"""
            <div class="chat-message other-message">
                <div class="message-sender">{sender_name}</div>
                <div>{message[3]}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        print(f"Error in display_message: {e}")
        # Don't crash the app, just skip this message
        return

def display_group_message(message):
    """Display a single group message with proper formatting"""
    try:
        # Safely extract timestamp
        timestamp = ''
        if message[4]:
            try:
                timestamp_parts = message[4].split(' ')
                if len(timestamp_parts) > 1 and len(timestamp_parts[1]) > 4:
                    timestamp = timestamp_parts[1][:5]
            except (IndexError, AttributeError):
                timestamp = ''
        
        if message[1] == st.session_state.current_user['username']:
            # User's message (right side)
            st.markdown(f"""
            <div class="chat-message user-message">
                <div>{message[3]}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Other user's message (left side)
            user_details = execute_query_one("SELECT first_name, last_name FROM users WHERE username = ?", (message[1],))
            sender_name = f"{user_details[0]} {user_details[1]}" if user_details else message[1]
            
            st.markdown(f"""
            <div class="chat-message other-message">
                <div class="message-sender">{sender_name}</div>
                <div>{message[3]}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        print(f"Error in display_group_message: {e}")
        return

# Enhanced chat renderers with smooth real-time functionality
def render_chat():
    st.header("💬 Advanced Chat System")
    
    # Auto-refresh settings
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.session_state.auto_refresh = st.checkbox("🔄 Enable Auto-refresh", value=st.session_state.auto_refresh)
    with col2:
        if st.button("🔄 Refresh Now", key="refresh_chat"):
            # Clear cache to force refresh
            if st.session_state.chat_type == 'private' and st.session_state.current_chat_user:
                cache_key = f"{st.session_state.current_user['username']}_{st.session_state.current_chat_user}"
                if cache_key in st.session_state.chat_messages:
                    del st.session_state.chat_messages[cache_key]
            elif st.session_state.chat_type == 'group' and st.session_state.current_chat_room:
                cache_key = f"room_{st.session_state.current_chat_room}"
                if cache_key in st.session_state.group_chat_messages:
                    del st.session_state.group_chat_messages[cache_key]
            st.rerun()
    with col3:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            if st.session_state.chat_type == 'private' and st.session_state.current_chat_user:
                cache_key = f"{st.session_state.current_user['username']}_{st.session_state.current_chat_user}"
                if cache_key in st.session_state.chat_messages:
                    del st.session_state.chat_messages[cache_key]
            elif st.session_state.chat_type == 'group' and st.session_state.current_chat_room:
                cache_key = f"room_{st.session_state.current_chat_room}"
                if cache_key in st.session_state.group_chat_messages:
                    del st.session_state.group_chat_messages[cache_key]
            st.rerun()
    
    # Chat type selection
    chat_type = st.radio("Chat Type", ["Private Chat", "Group Chat"], horizontal=True, key="chat_type_radio")
    st.session_state.chat_type = 'private' if chat_type == "Private Chat" else 'group'
    
    if st.session_state.chat_type == 'private':
        render_private_chat()
    else:
        render_group_chat()
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        # Use a more efficient auto-refresh approach
        if check_new_messages():
            st.rerun()

def render_private_chat():
    # Get users for chat (only approved users)
    users = execute_query("SELECT * FROM users WHERE status = 'approved' AND username != ?", 
                         (st.session_state.current_user['username'],), fetch=True)
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("👥 Contacts")
        
        # Search box for users
        search_term = st.text_input("🔍 Search users...", key="user_search")
        
        filtered_users = users
        if search_term:
            filtered_users = [u for u in users if search_term.lower() in f"{u[2]} {u[3]} {u[1]}".lower()]
        
        for user in filtered_users:
            display_name = f"{user[2]} {user[3]} ({user[8]})"
            # Show unread count badge
            unread_count = get_unread_private_count(st.session_state.current_user['username'], user[1])
            badge = f" 🔔{unread_count}" if unread_count > 0 else ""
            
            if st.button(f"{display_name}{badge}", key=f"contact_{user[1]}", use_container_width=True):
                st.session_state.current_chat_user = user[1]
                # Update last message ID when opening chat
                latest_message = execute_query_one(
                    "SELECT MAX(id) FROM messages WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)",
                    (st.session_state.current_user['username'], user[1], user[1], st.session_state.current_user['username'])
                )
                if latest_message and latest_message[0]:
                    st.session_state.last_message_id = latest_message[0]
                st.rerun()
        
        if not filtered_users:
            st.info("No users found")
    
    with col2:
        if st.session_state.current_chat_user:
            # Get user details
            user_details = execute_query_one("SELECT first_name, last_name, role FROM users WHERE username = ?", 
                                           (st.session_state.current_chat_user,))
            
            if user_details:
                st.subheader(f"💬 Chat with {user_details[0]} {user_details[1]} ({user_details[2]})")
                
                # Chat container with smooth scrolling
                chat_container = st.container()
                
                with chat_container:
                    # Get and display messages with caching
                    cache_key = f"{st.session_state.current_user['username']}_{st.session_state.current_chat_user}"
                    
                    if cache_key not in st.session_state.chat_messages:
                        st.session_state.chat_messages[cache_key] = get_private_messages(
                            st.session_state.current_user['username'], 
                            st.session_state.current_chat_user
                        )
                    
                    messages = st.session_state.chat_messages[cache_key]
                    
                    # Update last message ID
                    if messages:
                        st.session_state.last_message_id = messages[-1][0]
                    
                    # Display messages in a scrollable container
                    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
                    
                    for message in messages:
                        display_message(message)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Auto-refresh indicator
                if st.session_state.auto_refresh:
                    st.markdown('<div class="refresh-indicator">🔄 Auto-refreshing...</div>', unsafe_allow_html=True)
                
                # Chat input at bottom
                st.markdown("---")
                with st.form("private_chat_form", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        message_text = st.text_input("Type your message...", key="private_chat_input", 
                                                   placeholder="Type your message here...", label_visibility="collapsed")
                    with col2:
                        send_button = st.form_submit_button("📤 Send", use_container_width=True)
                    
                    if send_button and message_text.strip():
                        send_private_message(
                            st.session_state.current_user['username'],
                            st.session_state.current_chat_user,
                            message_text.strip()
                        )
                        # Clear cache to refresh messages
                        if cache_key in st.session_state.chat_messages:
                            del st.session_state.chat_messages[cache_key]
                        st.rerun()
            else:
                st.error("User not found")
                st.session_state.current_chat_user = None
        else:
            st.info("👈 Select a contact to start chatting")
            # Show recent conversations
            st.subheader("🕒 Recent Conversations")
            recent_chats = get_recent_private_chats(st.session_state.current_user['username'])
            if recent_chats:
                for chat in recent_chats[:5]:  # Show last 5 chats
                    other_user = chat[0] if chat[0] != st.session_state.current_user['username'] else chat[1]
                    user_details = execute_query_one("SELECT first_name, last_name FROM users WHERE username = ?", (other_user,))
                    if user_details:
                        if st.button(f"{user_details[0]} {user_details[1]}", key=f"recent_{other_user}", use_container_width=True):
                            st.session_state.current_chat_user = other_user
                            st.rerun()
            else:
                st.info("No recent conversations")

def render_group_chat():
    # Get chat rooms for current user
    rooms = get_chat_rooms()
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("👥 Chat Rooms")
        
        for room in rooms:
            room_name = f"#{room[1]}"
            # Show unread count badge
            unread_count = get_unread_group_count(room[0], st.session_state.current_user['username'])
            badge = f" 🔔{unread_count}" if unread_count > 0 else ""
            
            if st.button(f"{room_name}{badge}", key=f"room_{room[0]}", use_container_width=True):
                st.session_state.current_chat_room = room[0]
                # Update last message ID when opening room
                latest_message = execute_query_one(
                    "SELECT MAX(id) FROM group_messages WHERE room_id = ?",
                    (room[0],)
                )
                if latest_message and latest_message[0]:
                    st.session_state.last_group_message_id = latest_message[0]
                st.rerun()
        
        # Create new room (for admins and managers)
        if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager']:
            st.subheader("➕ Create Room")
            with st.form("create_room_form"):
                room_name = st.text_input("Room Name")
                room_description = st.text_input("Description")
                
                submit = st.form_submit_button("Create Room")
                
                if submit:
                    if room_name.strip():
                        execute_query('''
                            INSERT INTO chat_rooms (name, description, created_by)
                            VALUES (?, ?, ?)
                        ''', (room_name.strip(), room_description, st.session_state.current_user['username']))
                        
                        # Add creator to room
                        room_id = execute_query_one("SELECT id FROM chat_rooms WHERE name = ?", (room_name.strip(),))[0]
                        add_user_to_room(room_id, st.session_state.current_user['username'])
                        
                        st.success("✅ Room created successfully!")
                        st.rerun()
    
    with col2:
        if st.session_state.current_chat_room:
            room = execute_query_one("SELECT * FROM chat_rooms WHERE id = ?", (st.session_state.current_chat_room,))
            if room:
                st.subheader(f"💬 {room[1]}")
                st.caption(f"{room[2]} | Members: {get_room_member_count(room[0])}")
                
                # Chat container
                chat_container = st.container()
                
                with chat_container:
                    # Get and display group messages with caching
                    cache_key = f"room_{st.session_state.current_chat_room}"
                    
                    if cache_key not in st.session_state.group_chat_messages:
                        st.session_state.group_chat_messages[cache_key] = get_group_messages(st.session_state.current_chat_room)
                    
                    messages = st.session_state.group_chat_messages[cache_key]
                    
                    # Update last message ID
                    if messages:
                        st.session_state.last_group_message_id = messages[-1][0]
                    
                    # Display messages in a scrollable container
                    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
                    
                    for message in messages:
                        display_group_message(message)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Auto-refresh indicator
                if st.session_state.auto_refresh:
                    st.markdown('<div class="refresh-indicator">🔄 Auto-refreshing...</div>', unsafe_allow_html=True)
                
                # Room info and management
                with st.expander("👥 Room Info & Management"):
                    # Show room members
                    members = get_room_members(st.session_state.current_chat_room)
                    st.write("**Members:**")
                    for member in members:
                        user_details = execute_query_one("SELECT first_name, last_name, role FROM users WHERE username = ?", (member[0],))
                        if user_details:
                            st.write(f"- {user_details[0]} {user_details[1]} ({user_details[2]})")
                    
                    # Add user to room (for admins)
                    if st.session_state.current_user['role'] in ['superadmin', 'admin', 'manager']:
                        st.subheader("Add User to Room")
                        users = execute_query("SELECT username, first_name, last_name FROM users WHERE status = 'approved' AND username != ?", 
                                           (st.session_state.current_user['username'],), fetch=True)
                        user_options = [f"{u[1]} {u[2]} ({u[0]})" for u in users if u[0] not in [m[0] for m in members]]
                        
                        if user_options:
                            selected_user_display = st.selectbox("Select User to Add", user_options)
                            if st.button("➕ Add User", key="add_user_btn"):
                                selected_username = selected_user_display.split('(')[-1].replace(')', '')
                                add_user_to_room(st.session_state.current_chat_room, selected_username)
                                st.success(f"✅ User added to room!")
                                st.rerun()
                        
                        # Delete room option
                        if st.button("🗑️ Delete Room", key="delete_room_btn"):
                            execute_query("DELETE FROM chat_rooms WHERE id = ?", (st.session_state.current_chat_room,))
                            execute_query("DELETE FROM room_members WHERE room_id = ?", (st.session_state.current_chat_room,))
                            execute_query("DELETE FROM group_messages WHERE room_id = ?", (st.session_state.current_chat_room,))
                            st.session_state.current_chat_room = None
                            st.success("✅ Room deleted successfully!")
                            st.rerun()
                
                # Chat input at bottom
                st.markdown("---")
                with st.form("group_chat_form", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        message_text = st.text_input("Type your message...", key="group_chat_input", 
                                                   placeholder="Type your message here...", label_visibility="collapsed")
                    with col2:
                        send_button = st.form_submit_button("📤 Send", use_container_width=True)
                    
                    if send_button and message_text.strip():
                        send_group_message(
                            st.session_state.current_user['username'],
                            st.session_state.current_chat_room,
                            message_text.strip()
                        )
                        # Clear cache to refresh messages
                        if cache_key in st.session_state.group_chat_messages:
                            del st.session_state.group_chat_messages[cache_key]
                        st.rerun()
            else:
                st.error("Room not found")
                st.session_state.current_chat_room = None
        else:
            st.info("👈 Select a chat room to start group chatting")
            # Show available rooms info
            if rooms:
                st.subheader("Available Rooms")
                for room in rooms[:3]:  # Show first 3 rooms
                    member_count = get_room_member_count(room[0])
                    st.write(f"**#{room[1]}** - {member_count} members")
                    st.caption(room[2])

# Settings Page
def render_settings():
    st.header("⚙️ System Settings")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin']:
        st.error("❌ You don't have permission to access system settings.")
        return
    
    # Theme settings
    st.subheader("🎨 Theme Settings")
    current_theme = st.session_state.theme
    new_theme = st.selectbox("Select Theme", ["light", "dark"], index=0 if current_theme == "light" else 1)
    
    if new_theme != current_theme:
        if st.button("💾 Apply Theme", use_container_width=True, key="apply_theme_btn"):
            st.session_state.theme = new_theme
            st.success("✅ Theme applied successfully!")
            st.rerun()
    
    # System information
    st.subheader("💻 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        total_users = execute_query_one("SELECT COUNT(*) FROM users")[0] or 0
        st.metric("Total Users", total_users)
        
        total_products = execute_query_one("SELECT COUNT(*) FROM products")[0] or 0
        st.metric("Total Products", total_products)
    
    with col2:
        total_orders = execute_query_one("SELECT COUNT(*) FROM orders")[0] or 0
        st.metric("Total Orders", total_orders)
        
        total_messages = execute_query_one("SELECT COUNT(*) FROM messages")[0] or 0
        st.metric("Total Messages", total_messages)
    
    # Database maintenance
    st.subheader("🛠️ Database Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Messages", use_container_width=True, key="clear_messages_btn"):
            execute_query("DELETE FROM messages")
            execute_query("DELETE FROM group_messages")
            st.success("✅ All messages cleared successfully!")
    
    with col2:
        if st.button("🔄 Reset Demo Data", use_container_width=True, key="reset_data_btn"):
            # Clear all data except admin users
            execute_query("DELETE FROM products")
            execute_query("DELETE FROM orders")
            execute_query("DELETE FROM messages")
            execute_query("DELETE FROM group_messages")
            execute_query("DELETE FROM chat_rooms")
            execute_query("DELETE FROM room_members")
            execute_query("DELETE FROM pending_approvals")
            execute_query("DELETE FROM pending_profile_changes")
            execute_query("DELETE FROM role_upgrade_requests")
            execute_query("DELETE FROM users WHERE role NOT IN ('superadmin', 'admin')")
            
            # Reinitialize demo data
            init_database()
            st.success("✅ Demo data reset successfully!")
            st.rerun()

# Approvals Page
def render_approvals():
    st.header("✅ Approval Management")
    
    user = st.session_state.current_user
    
    if user['role'] not in ['superadmin', 'admin', 'manager', 'distributor', 'dealer', 'retailer']:
        st.error("❌ You don't have permission to access approval management.")
        return
    
    # Pending user approvals
    st.subheader("👥 Pending User Approvals")
    approvable_roles = get_approvable_users(user['role'])
    
    if approvable_roles:
        pending_users = execute_query(
            "SELECT * FROM users WHERE status = 'pending' AND role IN ({})".format(
                ','.join(['?'] * len(approvable_roles))
            ), approvable_roles, fetch=True
        )
        
        if pending_users:
            for u in pending_users:
                with st.container():
                    st.markdown(f"""
                    <div class="approval-item">
                        <h4>👤 {u[2]} {u[3]} ({u[1]})</h4>
                        <p><strong>Role:</strong> {u[8]} | <strong>Email:</strong> {u[4]} | <strong>Phone:</strong> {u[5]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve {u[1]}", key=f"approve_{u[0]}", use_container_width=True):
                            execute_query("UPDATE users SET status = 'approved' WHERE id = ?", (u[0],))
                            st.success(f"✅ User {u[1]} approved successfully!")
                            st.rerun()
                    
                    with col2:
                        if st.button(f"❌ Reject {u[1]}", key=f"reject_{u[0]}", use_container_width=True):
                            execute_query("DELETE FROM users WHERE id = ?", (u[0],))
                            st.success(f"✅ User {u[1]} rejected and deleted!")
                            st.rerun()
        else:
            st.info("ℹ️ No pending user approvals")
    else:
        st.info("ℹ️ You cannot approve any users at your current role level")
    
    # Pending role upgrade requests
    st.subheader("📈 Pending Role Upgrade Requests")
    pending_upgrades = get_pending_role_upgrades(user['role'])
    
    if pending_upgrades:
        for request in pending_upgrades:
            with st.container():
                st.markdown(f"""
                <div class="approval-item">
                    <h4>🔼 {request[8]} {request[9]} ({request[1]})</h4>
                    <p><strong>Current Role:</strong> {request[2]} | <strong>Requested Role:</strong> {request[3]}</p>
                    <p><strong>Reason:</strong> {request[4] or 'No reason provided'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve Upgrade", key=f"approve_upgrade_{request[0]}", use_container_width=True):
                        success, message = approve_role_upgrade(request[0], user['username'])
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                        st.rerun()
                
                with col2:
                    if st.button(f"❌ Reject Upgrade", key=f"reject_upgrade_{request[0]}", use_container_width=True):
                        success, message = reject_role_upgrade(request[0], user['username'])
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                        st.rerun()
    else:
        st.info("ℹ️ No pending role upgrade requests")

# Main app
def main():
    # Initialize session state and database
    init_session_state()
    try:
        init_database()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
    
    # Apply theme
    apply_theme()
    
    # Render header
    render_header()
    
    # Render sidebar if authenticated
    if st.session_state.authenticated:
        render_sidebar()
    
    # Render current page
    if not st.session_state.authenticated:
        if st.session_state.current_page == 'login':
            render_login()
        elif st.session_state.current_page == 'signup':
            render_signup()
    else:
        if st.session_state.current_page == 'dashboard':
            render_dashboard()
        elif st.session_state.current_page == 'profile':
            render_profile()
        elif st.session_state.current_page == 'user_management':
            render_user_management()
        elif st.session_state.current_page == 'products':
            render_products()
        elif st.session_state.current_page == 'orders':
            render_orders()
        elif st.session_state.current_page == 'stock':
            render_stock()
        elif st.session_state.current_page == 'reports':
            render_reports()
        elif st.session_state.current_page == 'chat':
            render_chat()
        elif st.session_state.current_page == 'settings':
            render_settings()
        elif st.session_state.current_page == 'approvals':
            render_approvals()

if __name__ == "__main__":
    main()