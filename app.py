import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import json
import os

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    if 'current_chat_user' not in st.session_state:
        st.session_state.current_chat_user = 'admin'

# Database setup
def init_database():
    try:
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
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

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

# Role hierarchy
role_hierarchy = {
    'admin': ['manager', 'distributor', 'dealer', 'retailer', 'user'],
    'manager': ['distributor', 'dealer', 'retailer', 'user'],
    'distributor': ['dealer', 'retailer', 'user'],
    'dealer': ['retailer', 'user'],
    'retailer': ['user']
}

# Authentication
def login_user(username, password, role):
    user = execute_query_one(
        "SELECT * FROM users WHERE username = ? AND role = ?", 
        (username, role)
    )
    if user and user[7] == password:
        if user[9] == 'approved' or user[8] == 'admin':
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
    existing_user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
    if existing_user:
        return False, "Username already exists"
    
    status = 'approved' if role == 'admin' else 'pending'
    
    execute_query('''
        INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, first_name, last_name, email, phone, id_number, password, role, status))
    
    return True, "Registration successful"

# Page navigation
def navigate_to(page):
    st.session_state.current_page = page

# UI Components
def render_header():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("Multi-Role Authentication System")
    with col2:
        if st.session_state.authenticated:
            st.write(f"Welcome, {st.session_state.current_user['first_name']}")
    with col3:
        if st.session_state.authenticated:
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.current_user = None
                st.session_state.current_page = 'login'
                st.rerun()

def render_sidebar():
    if st.session_state.authenticated:
        with st.sidebar:
            st.header("Navigation")
            
            if st.button("🏠 Dashboard"):
                navigate_to('dashboard')
            
            if st.button("👤 Profile"):
                navigate_to('profile')
            
            if st.session_state.current_user['role'] in role_hierarchy:
                if st.button("👥 Create User"):
                    navigate_to('create_user')
            
            if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
                if st.button("📦 Products"):
                    navigate_to('products')
                if st.button("🛒 Orders"):
                    navigate_to('orders')
            
            if st.button("💬 Chat"):
                navigate_to('chat')

# Page renderers
def render_login():
    st.header("Login")
    
    with st.form("login_form"):
        role = st.selectbox("Role", ["admin", "manager", "distributor", "dealer", "retailer", "user"])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
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
    if st.button("Sign Up"):
        navigate_to('signup')

def render_signup():
    st.header("Sign Up")
    
    with st.form("signup_form"):
        role = st.selectbox("Role", ["manager", "distributor", "dealer", "retailer", "user"])
        username = st.text_input("Username")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        id_number = st.text_input("ID Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign Up"):
            success, message = signup_user(role, username, first_name, last_name, email, phone, id_number, password)
            if success:
                st.success(message)
                navigate_to('login')
            else:
                st.error(message)
    
    st.write("Already have an account?")
    if st.button("Login"):
        navigate_to('login')

def render_dashboard():
    st.header("Dashboard")
    st.write(f"Welcome, {st.session_state.current_user['first_name']} {st.session_state.current_user['last_name']}!")
    st.write(f"Role: {st.session_state.current_user['role'].title()}")
    
    if st.session_state.current_user['role'] in ['admin', 'manager', 'distributor', 'dealer', 'retailer']:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_products = execute_query_one("SELECT COUNT(*) FROM products")[0]
            st.metric("Total Products", total_products)
        
        with col2:
            total_orders = execute_query_one("SELECT COUNT(*) FROM orders")[0]
            st.metric("Total Orders", total_orders)
        
        with col3:
            total_users = execute_query_one("SELECT COUNT(*) FROM users")[0]
            st.metric("Total Users", total_users)

def render_profile():
    st.header("Profile Management")
    
    user = st.session_state.current_user
    
    with st.form("profile_form"):
        st.text_input("Username", value=user['username'], disabled=True)
        first_name = st.text_input("First Name", value=user['first_name'])
        last_name = st.text_input("Last Name", value=user['last_name'])
        email = st.text_input("Email", value=user['email'])
        phone = st.text_input("Phone", value=user['phone'])
        id_number = st.text_input("ID Number", value=user['id_number'])
        
        if st.form_submit_button("Update Profile"):
            execute_query('''
                UPDATE users SET first_name=?, last_name=?, email=?, phone=?, id_number=?
                WHERE username=?
            ''', (first_name, last_name, email, phone, id_number, user['username']))
            
            st.session_state.current_user.update({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'id_number': id_number
            })
            
            st.success("Profile updated successfully!")

def render_create_user():
    st.header("Create User Account")
    
    allowed_roles = role_hierarchy.get(st.session_state.current_user['role'], [])
    
    with st.form("create_user_form"):
        role = st.selectbox("Role", allowed_roles)
        username = st.text_input("Username")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        id_number = st.text_input("ID Number")
        password = st.text_input("Password", type="password")
        
        if st.form_submit_button("Create User"):
            existing_user = execute_query_one("SELECT * FROM users WHERE username = ?", (username,))
            if existing_user:
                st.error("Username already exists")
            else:
                execute_query('''
                    INSERT INTO users (username, first_name, last_name, email, phone, id_number, password, role, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, first_name, last_name, email, phone, id_number, password, role, 'approved', st.session_state.current_user['username']))
                
                st.success(f"User {username} created successfully with role: {role}")

def render_products():
    st.header("Product Management")
    
    with st.expander("Add New Product"):
        with st.form("add_product_form"):
            name = st.text_input("Product Name")
            category = st.text_input("Category")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            stock = st.number_input("Stock", min_value=0)
            description = st.text_area("Description")
            
            if st.form_submit_button("Add Product"):
                execute_query('''
                    INSERT INTO products (name, category, price, stock, description, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, category, price, stock, description, st.session_state.current_user['username']))
                st.success(f"Product '{name}' added successfully")
                st.rerun()
    
    st.subheader("Product List")
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
                'Description': product[6]
            })
        
        df = pd.DataFrame(product_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No products found")

def render_orders():
    st.header("Order Management")
    
    with st.expander("Create New Order"):
        products = execute_query("SELECT * FROM products", fetch=True)
        customers = execute_query("SELECT * FROM users WHERE role = 'user' AND status = 'approved'", fetch=True)
        
        with st.form("create_order_form"):
            customer = st.selectbox("Customer", [f"{c[2]} {c[3]} ({c[1]})" for c in customers]) if customers else st.selectbox("Customer", [])
            product = st.selectbox("Product", [f"{p[1]} - ${p[3]:.2f} (Stock: {p[4]})" for p in products]) if products else st.selectbox("Product", [])
            quantity = st.number_input("Quantity", min_value=1, value=1)
            
            if st.form_submit_button("Create Order") and products and customers:
                product_id = products[[f"{p[1]} - ${p[3]:.2f} (Stock: {p[4]})" for p in products].index(product)][0]
                customer_username = customers[[f"{c[2]} {c[3]} ({c[1]})" for c in customers].index(customer)][1]
                
                product_data = execute_query_one("SELECT * FROM products WHERE id = ?", (product_id,))
                
                if product_data[4] < quantity:
                    st.error(f"Insufficient stock. Only {product_data[4]} units available.")
                else:
                    total = product_data[3] * quantity
                    
                    execute_query('''
                        INSERT INTO orders (customer, product_id, product_name, quantity, unit_price, total, date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (customer_username, product_id, product_data[1], quantity, product_data[3], total, date.today(), st.session_state.current_user['username']))
                    
                    execute_query('UPDATE products SET stock = stock - ? WHERE id = ?', (quantity, product_id))
                    
                    st.success("Order created successfully")
                    st.rerun()
    
    st.subheader("Order List")
    orders = execute_query("SELECT * FROM orders", fetch=True)
    
    if orders:
        order_data = []
        for order in orders:
            order_data.append({
                'ID': order[0],
                'Customer': order[1],
                'Product': order[3],
                'Quantity': order[4],
                'Total': f"${order[6]:.2f}",
                'Date': order[7],
                'Status': order[8]
            })
        
        df = pd.DataFrame(order_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No orders found")

def render_chat():
    st.header("Chat")
    
    users = execute_query("SELECT * FROM users WHERE status = 'approved'", fetch=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Contacts")
        for user in users:
            if user[1] != st.session_state.current_user['username']:
                if st.button(f"{user[2]} {user[3]} ({user[8]})", key=f"contact_{user[1]}", use_container_width=True):
                    st.session_state.current_chat_user = user[1]
                    st.rerun()
    
    with col2:
        if st.session_state.current_chat_user:
            st.subheader(f"Chat with {st.session_state.current_chat_user}")
            
            messages = execute_query('''
                SELECT * FROM messages 
                WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
                ORDER BY timestamp
            ''', (st.session_state.current_user['username'], st.session_state.current_chat_user, 
                  st.session_state.current_chat_user, st.session_state.current_user['username']), fetch=True)
            
            for message in messages:
                if message[1] == st.session_state.current_user['username']:
                    st.chat_message("user").write(message[3])
                else:
                    st.chat_message("assistant").write(f"**{message[1]}**: {message[3]}")
            
            message_text = st.chat_input("Type your message...")
            if message_text:
                execute_query('''
                    INSERT INTO messages (from_user, to_user, text)
                    VALUES (?, ?, ?)
                ''', (st.session_state.current_user['username'], st.session_state.current_chat_user, message_text))
                st.rerun()

# Main app
def main():
    init_session_state()
    
    if not init_database():
        st.error("Failed to initialize database")
        return
    
    render_header()
    
    if st.session_state.authenticated:
        render_sidebar()
    
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
        elif st.session_state.current_page == 'chat':
            render_chat()

if __name__ == "__main__":
    main()
