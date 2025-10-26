import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from database import init_db, Session, User, Product, Order, ChatMessage
from utils import authenticate_user, get_current_user, is_admin, get_dashboard_stats

# Page configuration
st.set_page_config(
    page_title="Dashboard System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom CSS for 3D effects and styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        animation: slideIn 0.3s ease-out;
    }
    
    .user-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        margin-left: 20%;
    }
    
    .other-message {
        background: rgba(255, 255, 255, 0.1);
        color: white;
        margin-right: 20%;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .online-user {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.25rem 0;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #4CAF50;
        border-radius: 50%;
        margin-right: 10px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
</style>
""", unsafe_allow_html=True)

# Authentication system
def login_page():
    st.markdown('<div class="main-header">🚀 Dashboard System</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### Login to Dashboard")
            
            with st.form("login_form"):
                username = st.text_input("👤 Username")
                password = st.text_input("🔒 Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
            st.markdown("---")
            st.markdown("**Demo Credentials:**")
            st.markdown("👑 **Admin:** `admin` / `admin123`")

# Main dashboard
def main_dashboard():
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 📊 Navigation")
        
        menu_options = [
            "🏠 Dashboard", "👤 Profile", "👥 User Management", 
            "📦 Products", "📋 Orders", "📊 Stock", 
            "📈 Reports", "💬 Chat", "⚙️ Settings", "✅ Approvals"
        ]
        
        selected_menu = st.radio("Go to", menu_options)
        
        st.markdown("---")
        user = get_current_user()
        if user:
            st.markdown(f"**Welcome, {user.username}!**")
            st.markdown(f"Role: {user.role}")
            
            if st.button("🚪 Logout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Dashboard content based on selection
    if selected_menu == "🏠 Dashboard":
        show_dashboard()
    elif selected_menu == "👤 Profile":
        show_profile()
    elif selected_menu == "👥 User Management":
        show_user_management()
    elif selected_menu == "📦 Products":
        show_products()
    elif selected_menu == "📋 Orders":
        show_orders()
    elif selected_menu == "📊 Stock":
        show_stock()
    elif selected_menu == "📈 Reports":
        show_reports()
    elif selected_menu == "💬 Chat":
        show_chat()
    elif selected_menu == "⚙️ Settings":
        show_settings()
    elif selected_menu == "✅ Approvals":
        show_approvals()

def show_dashboard():
    st.markdown('<div class="main-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)
    
    # Statistics cards
    stats = get_dashboard_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div>👥 Total Users</div>
            <div class="metric-value">{stats['total_users']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div>📦 Products</div>
            <div class="metric-value">{stats['total_products']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div>📋 Total Orders</div>
            <div class="metric-value">{stats['total_orders']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div>⏳ Pending Orders</div>
            <div class="metric-value">{stats['pending_orders']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("## 🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📦 Manage Products", use_container_width=True):
            st.session_state.menu = "📦 Products"
            st.rerun()
    
    with col2:
        if st.button("📋 View Orders", use_container_width=True):
            st.session_state.menu = "📋 Orders"
            st.rerun()
    
    with col3:
        if st.button("💬 Open Chat", use_container_width=True):
            st.session_state.menu = "💬 Chat"
            st.rerun()
    
    with col4:
        if st.button("📈 Generate Reports", use_container_width=True):
            st.session_state.menu = "📈 Reports"
            st.rerun()
    
    # Recent activity chart
    st.markdown("## 📈 Recent Activity")
    
    # Sample chart data
    dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='D')
    values = [100, 120, 110, 130, 125, 140, 150, 145, 160, 155, 170, 165, 180, 175, 190]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, fill='tozeroy', 
                           line=dict(color='#4facfe'), name='Activity'))
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_profile():
    st.markdown('<div class="main-header">👤 User Profile</div>', unsafe_allow_html=True)
    
    user = get_current_user()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Personal Information")
        st.text_input("Username", value=user.username, disabled=True)
        st.text_input("Email", value=user.email, disabled=True)
        st.text_input("Role", value=user.role, disabled=True)
        st.text_input("Member Since", value=user.created_at.strftime("%Y-%m-%d"), disabled=True)
    
    with col2:
        st.markdown("### Update Password")
        with st.form("update_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password"):
                if user.check_password(current_password):
                    if new_password == confirm_password:
                        user.set_password(new_password)
                        session = Session()
                        session.add(user)
                        session.commit()
                        session.close()
                        st.success("Password updated successfully!")
                    else:
                        st.error("New passwords don't match")
                else:
                    st.error("Current password is incorrect")

def show_user_management():
    if not is_admin():
        st.error("🔒 Access denied. Admin privileges required.")
        return
    
    st.markdown('<div class="main-header">👥 User Management</div>', unsafe_allow_html=True)
    
    # Add new user
    with st.expander("➕ Add New User"):
        with st.form("add_user"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username")
                new_email = st.text_input("Email")
            
            with col2:
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Create User"):
                session = Session()
                try:
                    if session.query(User).filter_by(username=new_username).first():
                        st.error("Username already exists")
                    elif session.query(User).filter_by(email=new_email).first():
                        st.error("Email already exists")
                    else:
                        user = User(username=new_username, email=new_email, role=new_role)
                        user.set_password(new_password)
                        session.add(user)
                        session.commit()
                        st.success("User created successfully!")
                finally:
                    session.close()
    
    # Users table
    st.markdown("### 📋 Users List")
    session = Session()
    users = session.query(User).all()
    session.close()
    
    users_data = []
    for user in users:
        users_data.append({
            'ID': user.id,
            'Username': user.username,
            'Email': user.email,
            'Role': user.role,
            'Created': user.created_at.strftime("%Y-%m-%d")
        })
    
    st.dataframe(users_data, use_container_width=True)

def show_products():
    st.markdown('<div class="main-header">📦 Product Management</div>', unsafe_allow_html=True)
    
    # Add new product
    with st.expander("➕ Add New Product"):
        with st.form("add_product"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Product Name")
                price = st.number_input("Price", min_value=0.0, format="%.2f")
                category = st.text_input("Category")
            
            with col2:
                stock_quantity = st.number_input("Stock Quantity", min_value=0)
                description = st.text_area("Description")
            
            if st.form_submit_button("Add Product"):
                session = Session()
                try:
                    product = Product(
                        name=name,
                        description=description,
                        price=price,
                        category=category,
                        stock_quantity=stock_quantity
                    )
                    session.add(product)
                    session.commit()
                    st.success("Product added successfully!")
                finally:
                    session.close()
    
    # Products table
    st.markdown("### 📋 Products List")
    session = Session()
    products = session.query(Product).all()
    session.close()
    
    products_data = []
    for product in products:
        products_data.append({
            'ID': product.id,
            'Name': product.name,
            'Category': product.category,
            'Price': f"${product.price:.2f}",
            'Stock': product.stock_quantity,
            'Created': product.created_at.strftime("%Y-%m-%d")
        })
    
    st.dataframe(products_data, use_container_width=True)

def show_orders():
    st.markdown('<div class="main-header">📋 Order Management</div>', unsafe_allow_html=True)
    
    # Create new order
    with st.expander("🛒 Create New Order"):
        session = Session()
        products = session.query(Product).all()
        session.close()
        
        product_names = [f"{p.name} (${p.price:.2f})" for p in products]
        
        with st.form("create_order"):
            selected_product = st.selectbox("Product", product_names)
            quantity = st.number_input("Quantity", min_value=1, value=1)
            
            if st.form_submit_button("Place Order"):
                product_index = product_names.index(selected_product)
                product = products[product_index]
                
                if product.stock_quantity >= quantity:
                    session = Session()
                    try:
                        order = Order(
                            user_id=get_current_user().id,
                            product_id=product.id,
                            quantity=quantity,
                            total_price=product.price * quantity
                        )
                        session.add(order)
                        session.commit()
                        st.success("Order placed successfully!")
                    finally:
                        session.close()
                else:
                    st.error("Insufficient stock!")
    
    # Orders table
    st.markdown("### 📋 Orders List")
    session = Session()
    orders = session.query(Order).join(User).join(Product).all()
    session.close()
    
    orders_data = []
    for order in orders:
        orders_data.append({
            'ID': order.id,
            'Customer': order.user.username,
            'Product': order.product.name,
            'Quantity': order.quantity,
            'Total': f"${order.total_price:.2f}",
            'Status': order.status,
            'Date': order.created_at.strftime("%Y-%m-%d")
        })
    
    st.dataframe(orders_data, use_container_width=True)

def show_stock():
    st.markdown('<div class="main-header">📊 Stock Management</div>', unsafe_allow_html=True)
    
    session = Session()
    products = session.query(Product).all()
    session.close()
    
    # Stock overview
    st.markdown("### 📈 Stock Overview")
    
    product_names = [p.name for p in products]
    stock_quantities = [p.stock_quantity for p in products]
    
    fig = px.bar(
        x=product_names,
        y=stock_quantities,
        title="Current Stock Levels",
        labels={'x': 'Products', 'y': 'Quantity'},
        color=stock_quantities,
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Stock table
    st.markdown("### 📋 Stock Details")
    stock_data = []
    for product in products:
        stock_data.append({
            'Product': product.name,
            'Current Stock': product.stock_quantity,
            'Price': f"${product.price:.2f}",
            'Category': product.category,
            'Last Updated': product.created_at.strftime("%Y-%m-%d")
        })
    
    st.dataframe(stock_data, use_container_width=True)

def show_reports():
    st.markdown('<div class="main-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    # Sample sales data
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    sales = [100 + i * 10 + (i % 7) * 20 for i in range(30)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sales trend
        fig1 = px.line(
            x=dates, y=sales,
            title="Sales Trend (Last 30 Days)",
            labels={'x': 'Date', 'y': 'Sales ($)'}
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Product performance (sample data)
        products = ['Laptop', 'Mouse', 'Keyboard', 'Monitor']
        performance = [45, 30, 15, 10]
        
        fig2 = px.pie(
            values=performance, names=products,
            title="Product Sales Distribution"
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Download report
    st.markdown("### 📊 Export Report")
    
    report_data = {
        'Date': dates,
        'Sales': sales
    }
    df_report = pd.DataFrame(report_data)
    
    st.download_button(
        label="📥 Download Sales Report (CSV)",
        data=df_report.to_csv(index=False),
        file_name="sales_report.csv",
        mime="text/csv"
    )

def show_chat():
    st.markdown('<div class="main-header">💬 3D Chat System</div>', unsafe_allow_html=True)
    
    # Initialize chat in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat messages container
        chat_container = st.container(height=500)
        
        with chat_container:
            for msg in st.session_state.chat_messages:
                if msg['user_id'] == get_current_user().id:
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You</strong> ({msg['time']}):<br>
                        {msg['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message other-message">
                        <strong>{msg['username']}</strong> ({msg['time']}):<br>
                        {msg['message']}
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        # Online users
        st.markdown("### 🟢 Online")
        st.markdown(f"""
        <div class="online-user">
            <div class="status-dot"></div>
            <span>{get_current_user().username}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample online users
        sample_users = ['Alice', 'Bob', 'Charlie']
        for user in sample_users:
            st.markdown(f"""
            <div class="online-user">
                <div class="status-dot"></div>
                <span>{user}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        message = st.text_input("Type your message...", key="chat_input")
    
    with col2:
        if st.button("Send", use_container_width=True):
            if message.strip():
                # Add message to session state
                new_message = {
                    'user_id': get_current_user().id,
                    'username': get_current_user().username,
                    'message': message.strip(),
                    'time': datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.chat_messages.append(new_message)
                
                # Also save to database
                session = Session()
                try:
                    chat_msg = ChatMessage(
                        user_id=get_current_user().id,
                        message=message.strip()
                    )
                    session.add(chat_msg)
                    session.commit()
                finally:
                    session.close()
                
                # Clear input
                st.session_state.chat_input = ""
                st.rerun()
    
    # Auto-refresh every 5 seconds
    if time.time() - st.session_state.last_update > 5:
        st.session_state.last_update = time.time()
        st.rerun()

def show_settings():
    st.markdown('<div class="main-header">⚙️ System Settings</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎨 Theme Settings")
        theme = st.selectbox("Color Theme", ["Dark", "Light", "Auto"])
        st.slider("Animation Speed", 1, 10, 5)
        st.toggle("Enable Notifications", value=True)
        st.toggle("Auto-refresh Data", value=True)
    
    with col2:
        st.markdown("### 🔒 Security Settings")
        st.toggle("Two-Factor Authentication", value=False)
        st.toggle("Session Timeout", value=True)
        st.number_input("Session Timeout (minutes)", min_value=5, max_value=120, value=30)
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved successfully!")

def show_approvals():
    if not is_admin():
        st.error("🔒 Access denied. Admin privileges required.")
        return
    
    st.markdown('<div class="main-header">✅ Approval System</div>', unsafe_allow_html=True)
    
    # Pending approvals
    st.markdown("### ⏳ Pending Approvals")
    
    session = Session()
    pending_orders = session.query(Order).filter_by(status='pending').all()
    session.close()
    
    for order in pending_orders:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**Order #{order.id}** - {order.product.name}")
                st.write(f"Quantity: {order.quantity} | Total: ${order.total_price:.2f}")
                st.write(f"Customer: {order.user.username}")
            
            with col2:
                if st.button(f"✅ Approve", key=f"approve_{order.id}"):
                    session = Session()
                    try:
                        order.status = 'approved'
                        session.add(order)
                        session.commit()
                        st.success(f"Order #{order.id} approved!")
                        st.rerun()
                    finally:
                        session.close()
            
            with col3:
                if st.button(f"❌ Reject", key=f"reject_{order.id}"):
                    session = Session()
                    try:
                        order.status = 'rejected'
                        session.add(order)
                        session.commit()
                        st.error(f"Order #{order.id} rejected!")
                        st.rerun()
                    finally:
                        session.close()
            
            st.markdown("---")

# Main app logic
def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()