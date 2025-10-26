import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import hashlib
import json
from typing import Dict, List, Optional
import random

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
        st.session_state.current_chat_user = 'admin'
    if 'current_chat_room' not in st.session_state:
        st.session_state.current_chat_room = None
    if 'chat_type' not in st.session_state:
        st.session_state.chat_type = 'private'

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
    
    # Messages table
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user TEXT NOT NULL,
            to_user TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Group messages table
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
        
        # Add admin to all rooms
        c.execute("SELECT id FROM chat_rooms")
        room_ids = [row[0] for row in c.fetchall()]
        for room_id in room_ids:
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

# Role hierarchy for user creation
role_hierarchy = {
    'admin': ['manager', 'distributor', 'dealer', 'retailer', 'user'],
    'manager': ['distributor', 'dealer', 'retailer', 'user'],
    'distributor': ['dealer', 'retailer', 'user'],
    'dealer': ['retailer', 'user'],
    'retailer': ['user']
}

# Approval hierarchy
approval_hierarchy = {
    'user': ['admin', 'manager', 'distributor', 'dealer', 'retailer'],
    'retailer': ['admin', 'manager', 'distributor', 'dealer'],
    'dealer': ['admin', 'manager', 'distributor'],
    'distributor': ['admin', 'manager'],
    'manager': ['admin']
}

# Color themes
def apply_theme():
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .main {
            background-color: #1a1a1a;
            color: #f0f0f0;
        }
        .stButton>button {
            background-color: #4a4a4a;
            color: white;
            border-radius: 10px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #5a5a5a;
        }
        .sidebar .sidebar-content {
            background-color: #2d2d2d;
        }
        .metric-card {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #4CAF50;
        }
        .chat-message {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .user-message {
            background-color: #2d2d2d;
            margin-left: 20%;
        }
        .other-message {
            background-color: #3d3d3d;
            margin-right: 20%;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .main {
            background-color: #f5f5f5;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 10px;
            border: none;
            padding: 10px 20px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .metric-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 5px solid #4CAF50;
        }
        .chat-message {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 20%;
        }
        .other-message {
            background-color: #f5f5f5;
            margin-right: 20%;
        }
        </style>
        """, unsafe_allow_html=True)

# Authentication functions
def login_user(username, password, role):
    user = execute_query_one(
        "SELECT * FROM users WHERE username = ? AND role = ?", 
        (username, role)
    )
    if user and user[7] == password:  # password is at index 7
        if user[9] == 'approved' or user[8] == 'admin':  # status at index 9, role at index 8
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
    return None

def signup_user(role, username, first_name, last_name, email, phone, id_number, password):
    # Check if username exists
    existing_user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
    if existing_user:
        return False, "Username already exists"
    
    # For admin, no approval needed
    status = 'approved' if role == 'admin' else 'pending'
    
    # Insert user
    execute_query('''
        INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, first_name, last_name, email, phone, id_number, password, role, status))
    
    # Get user ID for pending approval
    user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
    
    # Add to pending approvals if not admin
    if role != 'admin':
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
    
    return True, "Registration successful"

# Page navigation
def navigate_to(page):
    st.session_state.current_page = page

# UI Components
def render_header():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("<h1 style='color: #4CAF50;'>Multi-Role Authentication System</h1>", unsafe_allow_html=True)
    with col2:
        if st.session_state.authenticated:
            st.write(f"👋 Welcome, **{st.session_state.current_user['first_name']}**")
    with col3:
        if st.session_state.authenticated:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.current_page = 'login'
                st.rerun()
        # Theme toggle
        if st.button("🌙" if st.session_state.theme == 'light' else "☀️", use_container_width=True):
            st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'
            st.rerun()

def render_sidebar():
    if st.session_state.authenticated:
        with st.sidebar:
            st.markdown("<h2 style='color: #4CAF50;'>Navigation</h2>", unsafe_allow_html=True)
            
            # Dashboard
            if st.button("🏠 Dashboard", use_container_width=True):
                navigate_to('dashboard')
            
            # Profile
            if st.button("👤 Profile", use_container_width=True):
                navigate_to('profile')
            
            # User Management
            if st.session_state.current_user['role'] in role_hierarchy:
                if st.button("👥 Create User", use_container_width=True):
                    navigate_to('create_user')
            
            # Products, Orders, Stock, Reports (for business roles)
            if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
                if st.button("📦 Products", use_container_width=True):
                    navigate_to('products')
                if st.button("🛒 Orders", use_container_width=True):
                    navigate_to('orders')
                if st.button("📊 Stock", use_container_width=True):
                    navigate_to('stock')
                if st.button("📈 Reports", use_container_width=True):
                    navigate_to('reports')
            
            # Chat and Settings for all authenticated users
            if st.button("💬 Chat", use_container_width=True):
                navigate_to('chat')
            if st.button("⚙️ Settings", use_container_width=True):
                navigate_to('settings')
            
            # Approvals for roles that can approve
            if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
                if st.button("✅ Approvals", use_container_width=True):
                    navigate_to('approvals')

# Page renderers
def render_login():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Login</h1>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form", border=False):
                role = st.selectbox("Role", ["admin", "manager", "distributor", "dealer", "retailer", "user"])
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", use_container_width=True):
                    user = login_user(username, password, role)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.current_page = 'dashboard'
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials or account pending approval")
    
    st.write("Don't have an account?")
    if st.button("Sign Up", use_container_width=True):
        navigate_to('signup')

def render_signup():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Sign Up</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form", border=False):
        role = st.selectbox("Role", ["manager", "distributor", "dealer", "retailer", "user"])
        username = st.text_input("Username")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        id_number = st.text_input("ID Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign Up", use_container_width=True):
            success, message = signup_user(role, username, first_name, last_name, email, phone, id_number, password)
            if success:
                st.success(message)
                navigate_to('login')
            else:
                st.error(message)
    
    st.write("Already have an account?")
    if st.button("Login", use_container_width=True):
        navigate_to('login')

def render_dashboard():
    st.header("📊 Dashboard")
    st.write(f"Welcome, **{st.session_state.current_user['first_name']} {st.session_state.current_user['last_name']}**!")
    st.write(f"Role: **{st.session_state.current_user['role'].title()}**")
    
    # Display quick stats based on role
    if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_products = execute_query_one("SELECT COUNT(*) FROM products")[0]
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Products</h3>
                <h2>{total_products}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_orders = execute_query_one("SELECT COUNT(*) FROM orders")[0]
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Orders</h3>
                <h2>{total_orders}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_sales = execute_query_one("SELECT COALESCE(SUM(total), 0) FROM orders")[0]
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Sales</h3>
                <h2>${total_sales:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            low_stock = execute_query_one("SELECT COUNT(*) FROM products WHERE stock <= low_stock_alert")[0]
            st.markdown(f"""
            <div class="metric-card">
                <h3>Low Stock Items</h3>
                <h2>{low_stock}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick actions based on role
    st.subheader("🚀 Quick Actions")
    cols = st.columns(3)
    
    if st.session_state.current_user['role'] in role_hierarchy:
        with cols[0]:
            if st.button("👥 Create User", use_container_width=True):
                navigate_to('create_user')
    
    if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
        with cols[1]:
            if st.button("📦 Add Product", use_container_width=True):
                navigate_to('products')
        with cols[2]:
            if st.button("🛒 Create Order", use_container_width=True):
                navigate_to('orders')

def render_profile():
    st.header("👤 Profile Management")
    
    user = st.session_state.current_user
    
    with st.form("profile_form", border=False):
        st.text_input("Username", value=user['username'], disabled=True)
        first_name = st.text_input("First Name", value=user['first_name'])
        last_name = st.text_input("Last Name", value=user['last_name'])
        email = st.text_input("Email", value=user['email'])
        phone = st.text_input("Phone", value=user['phone'])
        id_number = st.text_input("ID Number", value=user['id_number'])
        new_password = st.text_input("New Password (leave blank to keep current)", type="password")
        
        if st.form_submit_button("Update Profile", use_container_width=True):
            # If admin, apply changes immediately
            if st.session_state.current_user['role'] == 'admin':
                execute_query('''
                    UPDATE users SET first_name=?, last_name=?, email=?, phone=?, id_number=?
                    WHERE username=?
                ''', (first_name, last_name, email, phone, id_number, user['username']))
                
                if new_password:
                    execute_query('UPDATE users SET password=? WHERE username=?', (new_password, user['username']))
                
                # Update session state
                st.session_state.current_user.update({
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'id_number': id_number
                })
                
                st.success("Profile updated successfully!")
            else:
                # For non-admin users, create profile change request
                execute_query('''
                    INSERT INTO pending_profile_changes (username, first_name, last_name, email, phone, id_number, password)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user['username'], first_name, last_name, email, phone, id_number, new_password if new_password else None))
                
                st.success("Profile changes submitted for approval. They will be applied once approved by an administrator.")

def render_create_user():
    st.header("👥 Create User Account")
    
    allowed_roles = role_hierarchy.get(st.session_state.current_user['role'], [])
    
    with st.form("create_user_form", border=False):
        role = st.selectbox("Role", allowed_roles)
        username = st.text_input("Username")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        id_number = st.text_input("ID Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Create User", use_container_width=True):
            # Check if username exists
            existing_user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
            if existing_user:
                st.error("Username already exists")
            else:
                # Create user (approved since created by higher role)
                execute_query('''
                    INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, first_name, last_name, email, phone, id_number, password, role, 'approved', st.session_state.current_user['username']))
                
                st.success(f"User {username} created successfully with role: {role}")

def render_products():
    st.header("📦 Product Management")
    
    # Add product form
    with st.expander("➕ Add New Product", expanded=False):
        with st.form("add_product_form", border=False):
            name = st.text_input("Product Name")
            category = st.text_input("Category")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            stock = st.number_input("Stock", min_value=0)
            description = st.text_area("Description")
            
            if st.form_submit_button("Add Product", use_container_width=True):
                execute_query('''
                    INSERT INTO products (name, category, price, stock, description, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, category, price, stock, description, st.session_state.current_user['username']))
                st.success(f"Product '{name}' added successfully")
                st.rerun()
    
    # Product list
    st.subheader("📋 Product List")
    products = execute_query("SELECT * FROM products", fetch=True)
    
    if products:
        product_data = []
        for product in products:
            product_data.append({
                'ID': product[0],
                'Name': product[1],
                'Category': product[2],
                'Price': f"${product[3]:.2f}",
                'Stock': product[4],
                'Low Stock Alert': product[5],
                'Description': product[6]
            })
        
        df = pd.DataFrame(product_data)
        st.dataframe(df, use_container_width=True)
        
        # Edit and delete options
        st.subheader("⚙️ Manage Products")
        col1, col2 = st.columns(2)
        
        with col1:
            product_ids = [p[0] for p in products]
            selected_product_id = st.selectbox("Select Product to Edit", product_ids, format_func=lambda x: f"{execute_query_one('SELECT name FROM products WHERE id = ?', (x,))[0]} (ID: {x})")
            
            if selected_product_id:
                product = execute_query_one("SELECT * FROM products WHERE id = ?", (selected_product_id,))
                with st.form("edit_product_form", border=False):
                    edit_name = st.text_input("Product Name", value=product[1])
                    edit_category = st.text_input("Category", value=product[2])
                    edit_price = st.number_input("Price", value=float(product[3]), format="%.2f")
                    edit_stock = st.number_input("Stock", value=product[4])
                    edit_description = st.text_area("Description", value=product[6])
                    
                    if st.form_submit_button("Update Product", use_container_width=True):
                        execute_query('''
                            UPDATE products SET name=?, category=?, price=?, stock=?, description=?
                            WHERE id=?
                        ''', (edit_name, edit_category, edit_price, edit_stock, edit_description, selected_product_id))
                        st.success("Product updated successfully")
                        st.rerun()
        
        with col2:
            delete_product_id = st.selectbox("Select Product to Delete", product_ids, format_func=lambda x: f"{execute_query_one('SELECT name FROM products WHERE id = ?', (x,))[0]} (ID: {x})", key="delete_select")
            
            if delete_product_id and st.button("🗑️ Delete Product", use_container_width=True, type="secondary"):
                execute_query("DELETE FROM products WHERE id = ?", (delete_product_id,))
                st.success("Product deleted successfully")
                st.rerun()
    else:
        st.info("No products found")

def render_orders():
    st.header("🛒 Order Management")
    
    # Create order form
    with st.expander("➕ Create New Order", expanded=False):
        # Get products for selection
        products = execute_query("SELECT * FROM products", fetch=True)
        customers = execute_query("SELECT * FROM users WHERE role = 'user' AND status = 'approved'", fetch=True)
        
        with st.form("create_order_form", border=False):
            customer = st.selectbox("Customer", [f"{c[2]} {c[3]} ({c[1]})" for c in customers])
            product = st.selectbox("Product", [f"{p[1]} - ${p[3]:.2f} (Stock: {p[4]})" for p in products])
            quantity = st.number_input("Quantity", min_value=1, value=1)
            notes = st.text_area("Order Notes")
            
            if st.form_submit_button("Create Order", use_container_width=True):
                # Extract product ID and customer username
                product_id = products[[f"{p[1]} - ${p[3]:.2f} (Stock: {p[4]})" for p in products].index(product)][0]
                customer_username = customers[[f"{c[2]} {c[3]} ({c[1]})" for c in customers].index(customer)][1]
                
                product_data = execute_query_one("SELECT * FROM products WHERE id = ?", (product_id,))
                
                if product_data[4] < quantity:  # Check stock
                    st.error(f"Insufficient stock. Only {product_data[4]} units available.")
                else:
                    total = product_data[3] * quantity
                    
                    # Create order
                    execute_query('''
                        INSERT INTO orders (customer, product_id, product_name, quantity, unit_price, total, date, notes, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (customer_username, product_id, product_data[1], quantity, product_data[3], total, date.today(), notes, st.session_state.current_user['username']))
                    
                    # Update product stock
                    execute_query('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
                    
                    st.success("Order created successfully")
                    st.rerun()
    
    # Order list
    st.subheader("📋 Order List")
    orders = execute_query("SELECT * FROM orders", fetch=True)
    
    if orders:
        order_data = []
        for order in orders:
            order_data.append({
                'ID': order[0],
                'Customer': order[1],
                'Product': order[3],
                'Quantity': order[4],
                'Unit Price': f"${order[5]:.2f}",
                'Total': f"${order[6]:.2f}",
                'Date': order[7],
                'Status': order[8],
                'Notes': order[9]
            })
        
        df = pd.DataFrame(order_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders found")

def render_stock():
    st.header("📊 Stock Management")
    
    products = execute_query("SELECT * FROM products", fetch=True)
    
    if products:
        for product in products:
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{product[1]}**")
                st.write(f"Category: {product[2]}")
                if product[4] <= product[5]:
                    st.error(f"Current Stock: **{product[4]}** - LOW STOCK!")
                else:
                    st.write(f"Current Stock: **{product[4]}**")
            
            with col2:
                new_stock = st.number_input("New Stock", min_value=0, value=product[4], key=f"stock_{product[0]}")
            
            with col3:
                if st.button("Update", key=f"update_{product[0]}", use_container_width=True):
                    execute_query('UPDATE products SET stock = ? WHERE id = ?', (new_stock, product[0]))
                    st.success(f"Stock updated for {product[1]}")
                    st.rerun()
            
            st.divider()
    else:
        st.info("No products found")

def render_reports():
    st.header("📈 Sales Reports")
    
    # Report type selection
    report_type = st.selectbox("Report Type", ["Daily", "Weekly", "Monthly"])
    report_date = st.date_input("Report Date", value=date.today())
    
    if st.button("Generate Report", use_container_width=True):
        # Generate sample report data (in a real app, this would query the database)
        st.subheader(f"{report_type} Report for {report_date}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Sales</h3>
                <h2>$12,456.78</h2>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Orders</h3>
                <h2>45</h2>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Average Order Value</h3>
                <h2>$276.82</h2>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>Top Product</h3>
                <h2>Laptop</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Sample chart
        st.subheader("Sales Trend")
        chart_data = pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Sales': [1200, 1900, 1500, 2100, 1800, 2200, 1950]
        })
        st.bar_chart(chart_data, x='Day', y='Sales')
        
        # Sample table
        st.subheader("Sales Breakdown")
        breakdown_data = pd.DataFrame({
            'Product': ['Laptop', 'Smartphone', 'Headphones', 'Tablet'],
            'Units Sold': [15, 28, 42, 12],
            'Revenue': ['$14,999.85', '$19,599.72', '$6,299.58', '$4,799.88'],
            'Growth': ['+12%', '+8%', '+15%', '+5%']
        })
        st.dataframe(breakdown_data, use_container_width=True)

# Chat functions
def get_chat_rooms():
    return execute_query('''
        SELECT cr.* FROM chat_rooms cr
        JOIN room_members rm ON cr.id = rm.room_id
        WHERE rm.username = ?
    ''', (st.session_state.current_user['username'],), fetch=True)

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

def render_chat():
    st.header("💬 Chat")
    
    # Chat type selection
    chat_type = st.radio("Chat Type", ["Private Chat", "Group Chat"], horizontal=True)
    
    if chat_type == "Private Chat":
        render_private_chat()
    else:
        render_group_chat()

def render_private_chat():
    # Get users for chat
    users = execute_query("SELECT * FROM users WHERE status = 'approved'", fetch=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Contacts")
        for user in users:
            if user[1] != st.session_state.current_user['username']:  # Don't show current user
                if st.button(f"{user[2]} {user[3]} ({user[8]})", key=f"contact_{user[1]}", use_container_width=True):
                    st.session_state.current_chat_user = user[1]
                    st.rerun()
    
    with col2:
        if st.session_state.current_chat_user:
            st.subheader(f"Chat with {st.session_state.current_chat_user}")
            
            # Display messages
            messages = execute_query('''
                SELECT * FROM messages 
                WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
                ORDER BY timestamp
            ''', (st.session_state.current_user['username'], st.session_state.current_chat_user, 
                  st.session_state.current_chat_user, st.session_state.current_user['username']), fetch=True)
            
            for message in messages:
                if message[1] == st.session_state.current_user['username']:
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You</strong>: {message[3]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message other-message">
                        <strong>{message[1]}</strong>: {message[3]}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Send message
            message_text = st.chat_input("Type your message...")
            if message_text:
                execute_query('''
                    INSERT INTO messages (from_user, to_user, text)
                    VALUES (?, ?, ?)
                ''', (st.session_state.current_user['username'], st.session_state.current_chat_user, message_text))
                st.rerun()

def render_group_chat():
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Chat Rooms")
        
        # Create new room
        with st.expander("➕ Create New Room"):
            with st.form("create_room_form", border=False):
                room_name = st.text_input("Room Name")
                room_description = st.text_input("Description")
                
                if st.form_submit_button("Create Room", use_container_width=True):
                    execute_query('''
                        INSERT INTO chat_rooms (name, description, created_by)
                        VALUES (?, ?, ?)
                    ''', (room_name, room_description, st.session_state.current_user['username']))
                    
                    # Add creator to the room
                    room_id = execute_query_one("SELECT id FROM chat_rooms WHERE name = ? AND created_by = ?", 
                                              (room_name, st.session_state.current_user['username']))[0]
                    execute_query('''
                        INSERT INTO room_members (room_id, username)
                        VALUES (?, ?)
                    ''', (room_id, st.session_state.current_user['username']))
                    
                    st.success(f"Room '{room_name}' created successfully!")
                    st.rerun()
        
        # List available rooms
        rooms = get_chat_rooms()
        if rooms:
            for room in rooms:
                if st.button(f"#{room[1]}", key=f"room_{room[0]}", use_container_width=True):
                    st.session_state.current_chat_room = room[0]
                    st.rerun()
        else:
            st.info("No chat rooms available")
    
    with col2:
        if st.session_state.current_chat_room:
            room = execute_query_one("SELECT * FROM chat_rooms WHERE id = ?", (st.session_state.current_chat_room,))
            st.subheader(f"#{room[1]}")
            st.caption(room[2])
            
            # Room management for room creator or admin
            if st.session_state.current_user['role'] == 'admin' or room[3] == st.session_state.current_user['username']:
                with st.expander("👥 Manage Room Members"):
                    users = execute_query("SELECT * FROM users WHERE status = 'approved'", fetch=True)
                    for user in users:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"{user[2]} {user[3]} ({user[1]})")
                        with col2:
                            if execute_query_one("SELECT * FROM room_members WHERE room_id = ? AND username = ?", 
                                               (st.session_state.current_chat_room, user[1])):
                                if st.button("Remove", key=f"remove_{user[1]}"):
                                    execute_query("DELETE FROM room_members WHERE room_id = ? AND username = ?", 
                                                (st.session_state.current_chat_room, user[1]))
                                    st.rerun()
                            else:
                                if st.button("Add", key=f"add_{user[1]}"):
                                    add_user_to_room(st.session_state.current_chat_room, user[1])
                                    st.rerun()
            
            # Display group messages
            messages = execute_query('''
                SELECT * FROM group_messages 
                WHERE room_id = ?
                ORDER BY timestamp
            ''', (st.session_state.current_chat_room,), fetch=True)
            
            for message in messages:
                if message[1] == st.session_state.current_user['username']:
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You</strong>: {message[3]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message other-message">
                        <strong>{message[1]}</strong>: {message[3]}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Send message to group
            message_text = st.chat_input("Type your message to the group...")
            if message_text:
                execute_query('''
                    INSERT INTO group_messages (from_user, room_id, text)
                    VALUES (?, ?, ?)
                ''', (st.session_state.current_user['username'], st.session_state.current_chat_room, message_text))
                st.rerun()
        else:
            st.info("Select a chat room to start chatting")

def render_settings():
    st.header("⚙️ Settings")
    
    # Notification settings
    st.subheader("🔔 Notification Settings")
    notification_setting = st.selectbox("Notifications", ["All Notifications", "Important Only", "None"])
    
    # Language settings
    language_setting = st.selectbox("Language", ["English", "Spanish", "French"])
    
    if st.button("Save Settings", use_container_width=True):
        st.success("Settings saved successfully")
    
    # Contact admin
    st.subheader("📞 Contact Admin")
    with st.form("contact_admin_form", border=False):
        subject = st.text_input("Subject")
        message_text = st.text_area("Message")
        
        if st.form_submit_button("Send Message to Admin", use_container_width=True):
            # Create a message to admin
            execute_query('''
                INSERT INTO messages (from_user, to_user, text)
                VALUES (?, ?, ?)
            ''', (st.session_state.current_user['username'], 'admin', f'[CONTACT] Subject: {subject}\n\n{message_text}'))
            
            st.success("Your message has been sent to admin")

def render_approvals():
    st.header("✅ Pending Approvals")
    
    # Pending user approvals
    st.subheader("👤 Pending User Approvals")
    pending_users = execute_query("SELECT * FROM users WHERE status = 'pending'", fetch=True)
    
    if pending_users:
        for user in pending_users:
            with st.expander(f"{user[2]} {user[3]} ({user[1]}) - {user[8]}"):
                st.write(f"**Email:** {user[4]}")
                st.write(f"**Phone:** {user[5]}")
                st.write(f"**ID Number:** {user[6]}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_{user[0]}", use_container_width=True):
                        if user[8] in approval_hierarchy and st.session_state.current_user['role'] in approval_hierarchy[user[8]]:
                            execute_query('UPDATE users SET status = ? WHERE id = ?', ('approved', user[0]))
                            st.success(f"User {user[1]} approved successfully")
                            st.rerun()
                        else:
                            st.error("You are not allowed to approve this user")
                with col2:
                    if st.button("Reject", key=f"reject_{user[0]}", use_container_width=True):
                        if user[8] in approval_hierarchy and st.session_state.current_user['role'] in approval_hierarchy[user[8]]:
                            execute_query('UPDATE users SET status = ? WHERE id = ?', ('rejected', user[0]))
                            st.success(f"User {user[1]} rejected")
                            st.rerun()
                        else:
                            st.error("You are not allowed to reject this user")
    else:
        st.info("No pending user approvals")
    
    # Pending profile changes
    st.subheader("📝 Pending Profile Changes")
    pending_changes = execute_query("SELECT * FROM pending_profile_changes", fetch=True)
    
    if pending_changes:
        for change in pending_changes:
            user = execute_query_one("SELECT * FROM users WHERE username = ?", (change[1],))
            
            with st.expander(f"Profile changes for {change[1]}"):
                if user:
                    st.write(f"**Current User:** {user[2]} {user[3]} ({user[8]})")
                
                st.write("**Proposed Changes:**")
                if change[2]:
                    st.write(f"- First Name: {change[2]}")
                if change[3]:
                    st.write(f"- Last Name: {change[3]}")
                if change[4]:
                    st.write(f"- Email: {change[4]}")
                if change[5]:
                    st.write(f"- Phone: {change[5]}")
                if change[6]:
                    st.write(f"- ID Number: {change[6]}")
                if change[7]:
                    st.write("- Password: *****")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Approve", key=f"approve_change_{change[0]}", use_container_width=True):
                        if user and user[8] in approval_hierarchy and st.session_state.current_user['role'] in approval_hierarchy[user[8]]:
                            # Apply changes
                            update_fields = []
                            update_values = []
                            
                            if change[2]:
                                update_fields.append("first_name = ?")
                                update_values.append(change[2])
                            if change[3]:
                                update_fields.append("last_name = ?")
                                update_values.append(change[3])
                            if change[4]:
                                update_fields.append("email = ?")
                                update_values.append(change[4])
                            if change[5]:
                                update_fields.append("phone = ?")
                                update_values.append(change[5])
                            if change[6]:
                                update_fields.append("id_number = ?")
                                update_values.append(change[6])
                            if change[7]:
                                update_fields.append("password = ?")
                                update_values.append(change[7])
                            
                            update_values.append(change[1])
                            
                            if update_fields:
                                execute_query(f'''
                                    UPDATE users SET {', '.join(update_fields)} 
                                    WHERE username = ?
                                ''', update_values)
                            
                            # Remove pending change
                            execute_query('DELETE FROM pending_profile_changes WHERE id = ?', (change[0],))
                            
                            st.success("Profile changes approved")
                            st.rerun()
                        else:
                            st.error("You are not allowed to approve these changes")
                with col2:
                    if st.button("Reject", key=f"reject_change_{change[0]}", use_container_width=True):
                        execute_query('DELETE FROM pending_profile_changes WHERE id = ?', (change[0],))
                        st.success("Profile changes rejected")
                        st.rerun()
    else:
        st.info("No pending profile changes")

# Main app
def main():
    # Initialize session state and database
    init_session_state()
    init_database()
    
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
        elif st.session_state.current_page == 'create_user':
            render_create_user()
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
