"""
Canadian Tax Optimizer - PROFESSIONAL EDITION with Advanced Analytics
Version 6.3.0 - Complete Analytics Dashboard

Professional application featuring:
- ✨ Institutional-grade user interface
- 👑 Advanced admin dashboard with 4 colored metric cards
- 📊 COMPLETE Analytics Dashboard (6 analytics modules)
- 🎨 Professional login page with animated branding
- 📈 User activity trends and engagement metrics
- 💰 Portfolio value growth over time
- 🎯 Tax optimization success rate tracking
- 📊 RRSP/TFSA contribution pattern analysis
- ⚠️ Contribution limit warnings
- 🏆 Top optimizers leaderboard
- 🔐 Multi-user authentication system
- 💼 All tax optimization features (RRSP, TFSA, multi-year planning)
- 📈 Portfolio tracking with growth projections
- 💡 Strategic insights and recommendations

Based on institutional portfolio management design principles
Ready for enterprise deployment on Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import hashlib
import secrets
import re
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback

# ============================================================================
# APP CONFIGURATION
# ============================================================================

APP_VERSION = "6.4.1 - POWER ADMIN & NOTIFICATIONS (Bug Fix)"
APP_DATE = "February 15, 2026"
APP_NAME = "Canadian Tax Optimizer"
APP_SUBTITLE = "Institutional-Grade RRSP & TFSA Planning Platform"

# Version Changelog
CHANGELOG = """
## 🎉 Version 6.4.1 - Bug Fix (Feb 15, 2026)

### 🐛 BUG FIXES:
- Fixed: "Add Year" button now works correctly
- Fixed: save_year_data() missing user_id parameter
- All year management functions now working properly

---

## 🎉 Version 6.4.0 - Power Admin & Notifications (Feb 15, 2026)

### ✨ NEW FEATURES:

**📊 Home Page Enhancements:**
- Quick Stats Cards: Total tax saved, total contributions, portfolio value
- Contribution Progress Bars: Visual room utilization for RRSP and TFSA
- Lifetime savings summary across all years

**👑 Admin Power Tools:**
- 🔐 Login as Any User: Admin impersonation to view user accounts
- 🔄 Reset User Data: Clear all planning years for any user
- 💣 Nuclear Database Reset: Delete ALL data and start fresh
- Enhanced user management controls

**📧 Email Notification System:**
- Welcome email when user creates account
- Tax year optimization alerts
- RRSP deadline reminders (30/60/90 days)
- Contribution limit warnings
- SMTP configuration in admin settings

**ℹ️ Version Info Page:**
- Accessible to all users via sidebar
- Complete changelog history
- Feature highlights
- Update notifications

### 🔧 Technical Improvements:
- Email templates with HTML formatting
- SMTP error handling and logging
- Session management for impersonation
- Safe database reset with confirmations

---

## Previous Versions:

### v6.3.2 - UI Fixes (Feb 14, 2026)
- Fixed white box on login page
- Fixed admin auto-creation logic
- Cleaned up login page styling

### v6.3.0 - Complete Analytics (Feb 14, 2026)
- User activity trends (30-day tracking)
- Portfolio growth visualization
- Tax optimization success tracking
- Contribution pattern analysis
- Limit warning system
- Top optimizers leaderboard

### v6.2.0 - Professional UI (Feb 13, 2026)
- Institutional-grade login page
- Purple gradient admin dashboard
- 4 colored metric cards
- Tab navigation system

### v6.1.0 - Multi-User Platform (Feb 12, 2026)
- PostgreSQL database integration
- Multi-user authentication
- Session management
- Auto-migration system
"""

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="TAX Optimization App",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# DATABASE CONNECTION POOL
# ============================================================================

class DatabasePool:
    """PostgreSQL connection pool singleton"""
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabasePool, cls).__new__(cls)
        return cls._instance
    
    def get_pool(self):
        """Get or create connection pool"""
        if self._pool is None:
            try:
                db_config = st.secrets["database"]
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=db_config["host"],
                    port=db_config["port"],
                    database=db_config["name"],
                    user=db_config["user"],
                    password=db_config["password"],
                    sslmode=db_config.get("sslmode", "require")
                )
            except Exception as e:
                st.error(f"Database connection failed: {str(e)}")
                st.stop()
        return self._pool

db_pool = DatabasePool()

def get_db_connection():
    """Get database connection from pool"""
    return db_pool.get_pool().getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    db_pool.get_pool().putconn(conn)

def execute_query(query, params=None, fetch=True, show_error=True):
    """Execute database query"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = None
        
        conn.commit()
        cursor.close()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        if show_error:
            st.error(f"Database error: {str(e)}")
        raise
    finally:
        if conn:
            return_db_connection(conn)

# ============================================================================
# AUTO-MIGRATION SYSTEM (creates tables automatically!)
# ============================================================================

class DatabaseMigration:
    """Automatic database migration - creates all tables on first run"""
    
    @staticmethod
    def get_schema_version():
        """Get current schema version from database"""
        try:
            result = execute_query(
                "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT 1",
                show_error=False  # Don't show error if table doesn't exist yet
            )
            return result[0]['version'] if result else 0
        except Exception:
            # Table doesn't exist yet - this is fine, return 0
            return 0
    
    @staticmethod
    def record_migration(version, description):
        """Record completed migration"""
        execute_query(
            "INSERT INTO schema_migrations (version, description, applied_at) VALUES (%s, %s, %s)",
            (version, description, datetime.now()),
            fetch=False
        )
    
    @staticmethod
    def run_migrations():
        """Run all pending migrations"""
        current_version = DatabaseMigration.get_schema_version()
        
        if current_version < 1:
            DatabaseMigration.migration_001_create_migrations_table()
            current_version = 1
        
        if current_version < 2:
            DatabaseMigration.migration_002_create_core_tables()
            current_version = 2
        
        if current_version < 3:
            DatabaseMigration.migration_003_add_phase2_tables()
            current_version = 3
        
        if current_version < 4:
            DatabaseMigration.migration_004_create_default_admin()
            current_version = 4
        
        return current_version
    
    @staticmethod
    def migration_001_create_migrations_table():
        """Migration 1: Create schema_migrations tracking table"""
        execute_query("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id SERIAL PRIMARY KEY,
                version INTEGER NOT NULL UNIQUE,
                description VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, fetch=False)
        
        execute_query(
            "INSERT INTO schema_migrations (version, description, applied_at) VALUES (1, 'Create schema_migrations table', %s)",
            (datetime.now(),),
            fetch=False
        )
    
    @staticmethod
    def migration_002_create_core_tables():
        """Migration 2: Create core application tables"""
        # Users table
        execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(64) NOT NULL,
                salt VARCHAR(32) NOT NULL,
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                login_attempts INTEGER DEFAULT 0,
                lockout_until TIMESTAMP,
                settings JSONB DEFAULT '{}'::JSONB,
                CONSTRAINT username_length CHECK (char_length(username) >= 3 AND char_length(username) <= 20),
                CONSTRAINT username_format CHECK (username ~ '^[a-zA-Z0-9_]+$')
            )
        """, fetch=False)
        
        # Indexes for users
        for idx in [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)"
        ]:
            execute_query(idx, fetch=False)
        
        # Tax planning table
        execute_query("""
            CREATE TABLE IF NOT EXISTS tax_planning_years (
                record_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                year INTEGER NOT NULL,
                data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_user_year UNIQUE(user_id, year),
                CONSTRAINT valid_year CHECK (year >= 2020 AND year <= 2100)
            )
        """, fetch=False)
        
        execute_query(
            "CREATE INDEX IF NOT EXISTS idx_tax_planning_user_id ON tax_planning_years(user_id)",
            fetch=False
        )
        
        # Sessions table
        execute_query("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                session_token VARCHAR(64) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """, fetch=False)
        
        # Login history
        execute_query("""
            CREATE TABLE IF NOT EXISTS login_history (
                history_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                failure_reason VARCHAR(255)
            )
        """, fetch=False)
        
        DatabaseMigration.record_migration(2, 'Create core tables')
    
    @staticmethod
    def migration_003_add_phase2_tables():
        """Migration 3: Add Phase 2 feature tables (email verification, admin audit)"""
        # Email verification tokens
        execute_query("""
            CREATE TABLE IF NOT EXISTS email_verification_tokens (
                token_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                token VARCHAR(64) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                used_at TIMESTAMP
            )
        """, fetch=False)
        
        # Password reset tokens
        execute_query("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                token VARCHAR(64) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                used_at TIMESTAMP
            )
        """, fetch=False)
        
        # Admin audit log
        execute_query("""
            CREATE TABLE IF NOT EXISTS admin_audit_log (
                log_id SERIAL PRIMARY KEY,
                admin_user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                action VARCHAR(100) NOT NULL,
                target_user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
                details JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """, fetch=False)
        
        DatabaseMigration.record_migration(3, 'Add Phase 2 tables')
    
    @staticmethod
    def migration_004_create_default_admin():
        """Migration 4: Create default admin account if no users exist"""
        # Check if any users exist
        try:
            users_count = execute_query("SELECT COUNT(*) as count FROM users", show_error=False)
            
            if users_count and users_count[0]['count'] == 0:
                # No users exist, create default admin
                admin_username = "admin"
                admin_email = "admin@taxoptimizer.local"
                admin_password = "admin123"
                
                # Hash password
                salt = secrets.token_hex(16)
                password_hash = hashlib.sha256((admin_password + salt).encode()).hexdigest()
                
                # Insert default admin
                execute_query("""
                    INSERT INTO users (username, email, password_hash, salt, role, is_active, created_at)
                    VALUES (%s, %s, %s, %s, 'admin', TRUE, %s)
                """, (admin_username, admin_email, password_hash, salt, datetime.now()), fetch=False)
                
                # Log success (this won't show but will be in logs)
                print(f"✅ Default admin account created: {admin_username} / {admin_password}")
        
        except Exception as e:
            # If users table doesn't exist yet, skip (will run after table creation)
            print(f"Skipping default admin creation: {e}")
        
        DatabaseMigration.record_migration(4, 'Create default admin account')

# Initialize database with auto-migrations
@st.cache_resource
def initialize_database():
    """Initialize database - creates tables automatically on first run!"""
    try:
        initial_version = DatabaseMigration.get_schema_version()
        
        if initial_version == 0:
            with st.spinner("🔄 Setting up database for first time..."):
                final_version = DatabaseMigration.run_migrations()
            st.success(f"✅ Database initialized successfully! All tables created.")
        else:
            final_version = DatabaseMigration.run_migrations()
            if final_version > initial_version:
                st.info(f"✅ Database updated to version {final_version}")
        
        return True
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        return False

# Run migrations automatically
initialize_database()

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def hash_password(password, salt=None):
    """Hash password with SHA-256 and salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt

def verify_password(password, stored_hash, salt):
    """Verify password against stored hash"""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == stored_hash

def generate_session_token():
    """Generate secure session token"""
    return secrets.token_urlsafe(32)

def validate_username(username):
    """Validate username format"""
    if not username or len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_email(email):
    """Validate email format"""
    if not email:
        return False, "Email is required"
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, "Invalid email format"
    return True, ""

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain a number"
    return True, ""

def register_user(username, email, password, confirm_password):
    """Register new user"""
    # Validate inputs
    is_valid, error = validate_username(username)
    if not is_valid:
        return False, error
    
    is_valid, error = validate_email(email)
    if not is_valid:
        return False, error
    
    is_valid, error = validate_password(password)
    if not is_valid:
        return False, error
    
    if password != confirm_password:
        return False, "Passwords do not match"
    
    # Check if username exists
    result = execute_query("SELECT COUNT(*) as count FROM users WHERE username = %s", (username,))
    if result[0]['count'] > 0:
        return False, "Username already taken"
    
    # Check if email exists
    result = execute_query("SELECT COUNT(*) as count FROM users WHERE email = %s", (email,))
    if result[0]['count'] > 0:
        return False, "Email already registered"
    
    # Hash password
    password_hash, salt = hash_password(password)
    
    # Determine role (first user = admin)
    result = execute_query("SELECT COUNT(*) as count FROM users")
    role = 'admin' if result[0]['count'] == 0 else 'user'
    
    # Create user
    execute_query(
        "INSERT INTO users (username, email, password_hash, salt, role) VALUES (%s, %s, %s, %s, %s)",
        (username, email, password_hash, salt, role),
        fetch=False
    )
    
    role_msg = " (Admin)" if role == 'admin' else ""
    
    # Send welcome email (if configured)
    try:
        send_welcome_email(username, email)
    except:
        pass  # Don't fail registration if email fails
    
    return True, f"Account created successfully{role_msg}! Please login."

# ============================================================================
# EMAIL NOTIFICATION SYSTEM
# ============================================================================

def get_smtp_config():
    """Get SMTP configuration from Streamlit secrets"""
    try:
        if hasattr(st, 'secrets') and 'email' in st.secrets:
            return {
                'enabled': st.secrets.email.get('enabled', False),
                'smtp_server': st.secrets.email.get('smtp_server', ''),
                'smtp_port': st.secrets.email.get('smtp_port', 587),
                'smtp_username': st.secrets.email.get('smtp_username', ''),
                'smtp_password': st.secrets.email.get('smtp_password', ''),
                'from_email': st.secrets.email.get('from_email', ''),
                'from_name': st.secrets.email.get('from_name', APP_NAME)
            }
        return {'enabled': False}
    except:
        return {'enabled': False}

def send_email(to_email, subject, html_body, plain_body=None):
    """Send email notification"""
    config = get_smtp_config()
    if not config.get('enabled'):
        return True, "Email disabled"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email
        
        if plain_body:
            msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['smtp_username'], config['smtp_password'])
            server.send_message(msg)
        
        return True, "Email sent"
    except Exception as e:
        return False, str(e)

def send_welcome_email(username, email):
    """Send welcome email to new user"""
    subject = f"Welcome to {APP_NAME}!"
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h1>🏦 Welcome to {APP_NAME}!</h1>
        </div>
        <div style="background: #f9fafb; padding: 30px; margin-top: 20px; border-radius: 10px;">
            <h2>Hello {username}! 👋</h2>
            <p>Your account has been created successfully!</p>
            <h3 style="color: #3b82f6;">🚀 Get Started:</h3>
            <ul>
                <li>Set up your first planning year</li>
                <li>Enter your income and contribution room</li>
                <li>Get instant tax optimization insights</li>
                <li>Track portfolio growth over time</li>
            </ul>
        </div>
        <div style="text-align: center; margin-top: 30px; color: #64748b;">
            <p>{APP_NAME} • {APP_SUBTITLE}</p>
        </div>
    </div>
    </body></html>
    """
    plain_body = f"Welcome to {APP_NAME}!\n\nHello {username}!\n\nYour account has been created successfully."
    return send_email(email, subject, html_body, plain_body)

def send_optimization_alert(username, email, year, taxable_income, threshold=181440):
    """Send tax optimization alert"""
    is_optimized = taxable_income < threshold
    subject = f"{'🎉' if is_optimized else '⚠️'} {year} Tax Year {'Optimized!' if is_optimized else 'Needs Work'}"
    status = "Optimized" if is_optimized else "Needs Optimization"
    color = "#10b981" if is_optimized else "#f59e0b"
    
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: {color}; color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h1>{year} Tax Year Update</h1>
            <p style="font-size: 18px;">Status: {status}</p>
        </div>
        <div style="background: #f9fafb; padding: 30px; margin-top: 20px; border-radius: 10px;">
            <h2>Hi {username},</h2>
            <p>Taxable Income: ${taxable_income:,.0f}<br>
            Penthouse Threshold: ${threshold:,.0f}</p>
        </div>
    </div>
    </body></html>
    """
    return send_email(email, subject, html_body)

def send_deadline_reminder(username, email, year, days_until, deadline_date):
    """Send RRSP deadline reminder"""
    urgency = "🔴 URGENT" if days_until <= 30 else "⚠️ IMPORTANT" if days_until <= 60 else "📅 REMINDER"
    subject = f"{urgency}: RRSP Deadline in {days_until} Days ({year})"
    
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #ef4444; color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h1>⏰ RRSP Deadline Reminder</h1>
            <p style="font-size: 24px; font-weight: 700;">{days_until} Days Remaining</p>
        </div>
        <div style="background: #f9fafb; padding: 30px; margin-top: 20px; border-radius: 10px;">
            <h2>Hi {username},</h2>
            <p>Tax Year: {year}<br>Deadline: {deadline_date}<br>Days Remaining: {days_until}</p>
        </div>
    </div>
    </body></html>
    """
    return send_email(email, subject, html_body)

def send_limit_warning(username, email, account_type, utilized_pct, remaining):
    """Send contribution limit warning"""
    subject = f"⚠️ Approaching {account_type} Limit ({utilized_pct:.0f}%)"
    
    html_body = f"""
    <html><body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: #f59e0b; color: white; padding: 30px; border-radius: 10px; text-align: center;">
            <h1>⚠️ Contribution Limit Alert</h1>
            <p>{utilized_pct:.0f}% Utilized</p>
        </div>
        <div style="background: #f9fafb; padding: 30px; margin-top: 20px; border-radius: 10px;">
            <h2>Hi {username},</h2>
            <p>Account: {account_type}<br>Utilization: {utilized_pct:.1f}%<br>Remaining: ${remaining:,.0f}</p>
        </div>
    </div>
    </body></html>
    """
    return send_email(email, subject, html_body)

def login_user(username_or_email, password):
    """Authenticate user and create session"""
    # Get user
    result = execute_query("SELECT * FROM users WHERE username = %s OR email = %s", 
                          (username_or_email, username_or_email))
    
    if not result:
        return False, "Invalid username/email or password", None
    
    user = dict(result[0])
    
    # Check if active
    if not user['is_active']:
        return False, "Account is deactivated", None
    
    # Check if locked
    if user['lockout_until'] and user['lockout_until'] > datetime.now():
        remaining = (user['lockout_until'] - datetime.now()).seconds // 60
        return False, f"Account locked. Try again in {remaining} minutes.", None
    
    # Verify password
    if not verify_password(password, user['password_hash'], user['salt']):
        # Increment failed attempts
        execute_query(
            "UPDATE users SET login_attempts = login_attempts + 1 WHERE user_id = %s",
            (user['user_id'],),
            fetch=False
        )
        
        # Lock if too many attempts
        if user['login_attempts'] + 1 >= 5:
            lockout_until = datetime.now() + timedelta(minutes=30)
            execute_query(
                "UPDATE users SET lockout_until = %s WHERE user_id = %s",
                (lockout_until, user['user_id']),
                fetch=False
            )
            return False, "Too many failed attempts. Account locked for 30 minutes.", None
        
        attempts_left = 5 - (user['login_attempts'] + 1)
        return False, f"Invalid username/email or password. {attempts_left} attempts remaining.", None
    
    # Successful login
    execute_query(
        "UPDATE users SET login_attempts = 0, lockout_until = NULL, last_login = %s WHERE user_id = %s",
        (datetime.now(), user['user_id']),
        fetch=False
    )
    
    # Create session
    session_token = generate_session_token()
    expires_at = datetime.now() + timedelta(minutes=60)
    execute_query(
        "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
        (user['user_id'], session_token, expires_at),
        fetch=False
    )
    
    # Record login
    execute_query(
        "INSERT INTO login_history (user_id, success) VALUES (%s, %s)",
        (user['user_id'], True),
        fetch=False
    )
    
    user_data = {
        'user_id': user['user_id'],
        'username': user['username'],
        'email': user['email'],
        'role': user['role'],
        'session_token': session_token
    }
    
    return True, "Login successful!", user_data

def verify_session(session_token):
    """Verify if session is valid"""
    if not session_token:
        return False, None
    
    result = execute_query(
        """SELECT s.*, u.* FROM user_sessions s 
           JOIN users u ON s.user_id = u.user_id
           WHERE s.session_token = %s AND s.is_active = TRUE AND s.expires_at > %s""",
        (session_token, datetime.now())
    )
    
    if not result:
        return False, None
    
    session = dict(result[0])
    
    # Update last activity
    execute_query(
        "UPDATE user_sessions SET last_activity = %s WHERE session_token = %s",
        (datetime.now(), session_token),
        fetch=False
    )
    
    user_data = {
        'user_id': session['user_id'],
        'username': session['username'],
        'email': session['email'],
        'role': session['role'],
        'session_token': session_token
    }
    
    return True, user_data

def logout_user(session_token):
    """Logout user by invalidating session"""
    if session_token:
        execute_query(
            "UPDATE user_sessions SET is_active = FALSE WHERE session_token = %s",
            (session_token,),
            fetch=False
        )

def change_password(user_id, current_password, new_password, confirm_password):
    """Change user password"""
    # Get user
    result = execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
    if not result:
        return False, "User not found"
    
    user = dict(result[0])
    
    # Verify current password
    if not verify_password(current_password, user['password_hash'], user['salt']):
        return False, "Current password is incorrect"
    
    # Validate new password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        return False, error
    
    if new_password != confirm_password:
        return False, "New passwords do not match"
    
    if current_password == new_password:
        return False, "New password must be different"
    
    # Hash new password
    new_hash, new_salt = hash_password(new_password)
    
    # Update password
    execute_query(
        "UPDATE users SET password_hash = %s, salt = %s WHERE user_id = %s",
        (new_hash, new_salt, user_id),
        fetch=False
    )
    
    # Invalidate all sessions
    execute_query(
        "UPDATE user_sessions SET is_active = FALSE WHERE user_id = %s",
        (user_id,),
        fetch=False
    )
    
    return True, "Password changed successfully. Please login again."

# ============================================================================
# DATA FUNCTIONS (PostgreSQL instead of JSON)
# ============================================================================

def load_all_data(user_id):
    """Load all year data for user"""
    result = execute_query(
        "SELECT year, data FROM tax_planning_years WHERE user_id = %s ORDER BY year",
        (user_id,)
    )
    if result:
        return {str(row['year']): row['data'] for row in result}
    return {}

def save_year_data(user_id, year, data):
    """Save year data for user"""
    try:
        data_json = json.dumps(data)
        execute_query(
            """INSERT INTO tax_planning_years (user_id, year, data)
               VALUES (%s, %s, %s)
               ON CONFLICT (user_id, year) 
               DO UPDATE SET data = %s, updated_at = CURRENT_TIMESTAMP""",
            (user_id, year, data_json, data_json),
            fetch=False
        )
        return True
    except:
        return False

def delete_year_data(user_id, year):
    """Delete year data for user"""
    try:
        execute_query(
            "DELETE FROM tax_planning_years WHERE user_id = %s AND year = %s",
            (user_id, year),
            fetch=False
        )
        return True
    except:
        return False

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state"""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "email" not in st.session_state:
        st.session_state.email = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "session_token" not in st.session_state:
        st.session_state.session_token = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Home"
    if "selected_year" not in st.session_state:
        st.session_state.selected_year = 2025
    if "saved_flag" not in st.session_state:
        st.session_state.saved_flag = False

init_session_state()

# Check session validity
if st.session_state.logged_in and st.session_state.session_token:
    is_valid, user_data = verify_session(st.session_state.session_token)
    if not is_valid:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.role = None
        st.session_state.session_token = None
        st.rerun()

# ============================================================================
# STYLING
# ============================================================================

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    .premium-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    .desc-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);
    }
    
    .desc-box h4 {
        margin-top: 0;
        color: white;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    
    h1, h2, h3 {
        font-weight: 600;
        color: #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

def description_box(title, content):
    """Render premium description box"""
    st.markdown(f'''
        <div class="desc-box">
            <h4>{title}</h4>
            <div style="line-height:1.7; font-weight: 300;">{content}</div>
        </div>
    ''', unsafe_allow_html=True)

# ============================================================================
# TAX CALCULATION ENGINE (from v5)
# ============================================================================

TAX_BRACKETS = [
    {"name": "Floor 1", "low": 0, "high": 53891, "rate": 0.2005},
    {"name": "Floor 2", "low": 53891, "high": 58523, "rate": 0.2415},
    {"name": "Floor 3", "low": 58523, "high": 94907, "rate": 0.2965},
    {"name": "Floor 4", "low": 94907, "high": 117045, "rate": 0.3148},
    {"name": "Floor 5", "low": 117045, "high": 181440, "rate": 0.3389},
    {"name": "Penthouse", "low": 181440, "high": float('inf'), "rate": 0.4797}
]

def calculate_tax_on_income(income):
    if income <= 0:
        return 0
    total_tax = 0
    for bracket in TAX_BRACKETS:
        if income > bracket['low']:
            taxable_in_bracket = min(income, bracket['high']) - bracket['low']
            total_tax += taxable_in_bracket * bracket['rate']
    return total_tax

def calculate_tax_refund(gross_income, rrsp_contributions):
    if gross_income <= 0:
        return 0
    tax_without_rrsp = calculate_tax_on_income(gross_income)
    tax_with_rrsp = calculate_tax_on_income(gross_income - rrsp_contributions)
    refund = tax_without_rrsp - tax_with_rrsp
    return max(0, refund)

def get_marginal_rate(income):
    if income <= 0:
        return 0
    for bracket in TAX_BRACKETS:
        if bracket['low'] <= income < bracket['high']:
            return bracket['rate']
    return TAX_BRACKETS[-1]['rate']

def calculate_annual_rrsp(data):
    base_salary = data.get('base_salary', 0)
    biweekly_pct = data.get('biweekly_pct', 0)
    employer_match_cap = data.get('employer_match', 0)
    employee_contrib = base_salary * (biweekly_pct / 100)
    employer_contrib = base_salary * (min(biweekly_pct, employer_match_cap) / 100)
    periodic_rrsp = employee_contrib + employer_contrib
    lump_sum = data.get('rrsp_lump_sum_optimization', 0) + \
                data.get('rrsp_lump_sum_additional', 0) + \
                data.get('rrsp_lump_sum', 0)
    return periodic_rrsp + lump_sum

def get_rrsp_deadline(tax_year):
    deadline_year = tax_year + 1
    deadline_date = datetime(deadline_year, 3, 1)
    weekday = deadline_date.weekday()
    
    if weekday == 5:  # Saturday
        deadline_date += timedelta(days=2)
        weekend_note = " (Monday, as March 1st is Saturday)"
    elif weekday == 6:  # Sunday
        deadline_date += timedelta(days=1)
        weekend_note = " (Monday, as March 1st is Sunday)"
    else:
        weekend_note = ""
    
    formatted_date = deadline_date.strftime("%B %d, %Y")
    today = datetime.now()
    days_until = (deadline_date - today).days
    
    return deadline_date, formatted_date + weekend_note, days_until

def is_year_optimized(year_data):
    if not year_data:
        return False
    t4_gross = year_data.get('t4_gross_income', 0)
    other_inc = year_data.get('other_income', 0)
    total_gross = t4_gross + other_inc
    total_rrsp = calculate_annual_rrsp(year_data)
    taxable_income = max(0, total_gross - total_rrsp)
    penthouse_threshold = 181440
    return taxable_income <= penthouse_threshold

# ============================================================================
# LOGIN/REGISTER PAGE
# ============================================================================

def show_auth_page():
    """Display professional institutional-grade login page"""
    
    # AUTO-CREATE DEFAULT ADMIN if 'admin' user doesn't exist
    try:
        admin_check = execute_query(
            "SELECT COUNT(*) as count FROM users WHERE username = 'admin'", 
            show_error=False
        )
        
        if admin_check and admin_check[0]['count'] == 0:
            # 'admin' user doesn't exist - create it now
            admin_password = "admin123"
            password_hash, salt = hash_password(admin_password)
            
            execute_query("""
                INSERT INTO users (username, email, password_hash, salt, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, 'admin', TRUE, %s)
            """, ('admin', 'admin@taxoptimizer.local', password_hash, salt, datetime.now()), 
            fetch=False, show_error=False)
    except Exception:
        # Tables might not exist yet - ignore
        pass
    
    # Professional header with icon and title
    st.markdown(f"""
        <div style="text-align: center; padding: 60px 0 40px 0;">
            <div style="font-size: 5em; margin-bottom: 20px;">🏦</div>
            <h1 style="font-size: 2.8em; font-weight: 800; color: #1e293b; margin-bottom: 12px; letter-spacing: -0.5px;">
                {APP_NAME}
            </h1>
            <p style="font-size: 1.15em; color: #64748b; font-weight: 500; margin-bottom: 40px;">
                {APP_SUBTITLE}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])
    
    # LOGIN TAB
    with tab1:
        st.markdown("### Sign In to Your Account")
        st.markdown("")
        
        with st.form("login_form"):
            username_or_email = st.text_input("Username or Email", placeholder="Enter your username or email", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            
            st.markdown("")
            login_button = st.form_submit_button("🔐 Sign In", use_container_width=True, type="primary")
            
            if login_button:
                if not username_or_email or not password:
                    st.error("⚠️ Please enter both username/email and password")
                else:
                    success, message, user_data = login_user(username_or_email, password)
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_data['user_id']
                        st.session_state.username = user_data['username']
                        st.session_state.email = user_data['email']
                        st.session_state.role = user_data['role']
                        st.session_state.session_token = user_data['session_token']
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    # REGISTER TAB
    with tab2:
        st.markdown("### Create Your Account")
        st.markdown("")
        
        with st.form("register_form"):
            new_username = st.text_input("Username", placeholder="3-20 characters, letters and numbers", key="reg_user")
            new_email = st.text_input("Email Address", placeholder="your@email.com", key="reg_email")
            new_password = st.text_input("Password", type="password", placeholder="Minimum 8 characters", key="reg_pass")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password", key="reg_confirm")
            
            st.markdown("")
            register_button = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")
            
            if register_button:
                success, message = register_user(new_username, new_email, new_password, confirm_password)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
    
    # First time setup help
    st.markdown("")
    with st.expander("ℹ️ First time setup?", expanded=False):
        st.info("""
            **Default Admin Account:**
            
            Username: `admin`  
            Password: `admin123`
            
            ⚠️ **Important:** Change the admin password immediately after first login for security.
        """)
    
    # Professional footer
    st.markdown(f"""
        <div style="text-align: center; color: #94a3b8; font-size: 0.9em; margin-top: 60px; padding: 30px 20px;">
            <p style="font-weight: 600; color: #64748b; margin-bottom: 8px;">{APP_NAME} • {APP_VERSION}</p>
            <p style="font-size: 0.85em; margin: 4px 0;">
                Built: {APP_DATE} • Professional Edition • Multi-User Platform
            </p>
            <p style="font-size: 0.8em; margin: 8px 0 0 0; color: #cbd5e1;">
                Tax rates: 2025/2026 Ontario (Federal + Provincial) • Auto-Migration Enabled • PostgreSQL Powered
            </p>
        </div>
    """, unsafe_allow_html=True)

# ============================================================================
# ADMIN DASHBOARD PAGE
# ============================================================================

def show_admin_dashboard():
    """Display professional institutional-grade admin dashboard"""
    
    with st.sidebar:
        if st.button("⬅️ Back to App", use_container_width=True, key="admin_back_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="admin_logout_btn"):
            logout_user(st.session_state.session_token)
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.email = None
            st.session_state.role = None
            st.session_state.session_token = None
            st.rerun()
    
    # PROFESSIONAL HEADER BANNER (Purple Gradient - Matching Reference Image 2)
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             color: white; padding: 40px; border-radius: 16px; margin-bottom: 32px; 
             box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);">
            <h1 style="margin: 0; font-size: 2.2em; font-weight: 700; color: white;">
                👑 Administrator Dashboard
            </h1>
            <p style="margin: 12px 0 0 0; font-size: 1.15em; opacity: 0.95; color: white; font-weight: 500;">
                System Overview & Management
            </p>
            <p style="margin: 8px 0 0 0; font-size: 0.95em; opacity: 0.9; color: white;">
                Complete administrative control and monitoring dashboard
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Get comprehensive statistics
    try:
        stats_query = """
            SELECT 
                COUNT(*) as total_users,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_users,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admin_users
            FROM users
        """
        stats = execute_query(stats_query)
        
        # Count planning years
        years_query = "SELECT COUNT(*) as total_years FROM tax_planning_years"
        years_data = execute_query(years_query)
        
        # Count years needing optimization (Penthouse exposure)
        needs_action_query = """
            SELECT COUNT(*) as needs_action 
            FROM tax_planning_years 
            WHERE (COALESCE((data->>'t4_gross_income')::numeric, 0) + 
                   COALESCE((data->>'other_income')::numeric, 0) - 
                   COALESCE((data->>'rrsp_lump_sum_optimization')::numeric, 0) - 
                   COALESCE((data->>'rrsp_lump_sum_additional')::numeric, 0) -
                   (COALESCE((data->>'base_salary')::numeric, 0) * 
                    (COALESCE((data->>'biweekly_pct')::numeric, 0) + 
                     COALESCE((data->>'employer_match')::numeric, 0)) / 100)) > 181440
        """
        needs_action_data = execute_query(needs_action_query)
        
        # Calculate total portfolio value
        portfolio_query = """
            SELECT SUM(COALESCE((data->>'rrsp_balance_start')::numeric, 0) + 
                      COALESCE((data->>'tfsa_balance_start')::numeric, 0)) as total_aum
            FROM tax_planning_years
        """
        portfolio_data = execute_query(portfolio_query)
        
        if stats:
            # LARGE COLORED METRIC CARDS (Matching Reference Image 2)
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                         color: white; padding: 36px 24px; border-radius: 16px; text-align: center;
                         box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.5);">
                        <div style="font-size: 3.8em; font-weight: 800; margin: 10px 0; line-height: 1;">{stats[0]['total_users']}</div>
                        <div style="font-size: 0.95em; font-weight: 600; opacity: 0.95; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 8px;">Total Users</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                total_years = years_data[0]['total_years'] if years_data else 0
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                         color: white; padding: 36px 24px; border-radius: 16px; text-align: center;
                         box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.5);">
                        <div style="font-size: 3.8em; font-weight: 800; margin: 10px 0; line-height: 1;">{total_years}</div>
                        <div style="font-size: 0.95em; font-weight: 600; opacity: 0.95; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 8px;">Total Planning Years</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col3:
                needs_action = needs_action_data[0]['needs_action'] if needs_action_data else 0
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                         color: white; padding: 36px 24px; border-radius: 16px; text-align: center;
                         box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.5);">
                        <div style="font-size: 3.8em; font-weight: 800; margin: 10px 0; line-height: 1;">{needs_action}</div>
                        <div style="font-size: 0.95em; font-weight: 600; opacity: 0.95; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 8px;">Need Optimization</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col4:
                total_aum = portfolio_data[0]['total_aum'] if portfolio_data and portfolio_data[0]['total_aum'] else 0
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                         color: white; padding: 36px 24px; border-radius: 16px; text-align: center;
                         box-shadow: 0 4px 6px -1px rgba(139, 92, 246, 0.5);">
                        <div style="font-size: 2.8em; font-weight: 800; margin: 10px 0; line-height: 1;">${total_aum:,.0f}</div>
                        <div style="font-size: 0.95em; font-weight: 600; opacity: 0.95; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 8px;">Total Portfolio Value</div>
                    </div>
                """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    
    st.divider()
    
    # TAB NAVIGATION (Matching Reference Image 2)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 All Users Overview", "👥 User Management", "📈 System Analytics", "⚡ Power Tools"])
    
    with tab1:
        st.markdown("### 📊 All Users Overview")
        st.caption("Complete view of all user profiles across the system")
        
        try:
            users_query = """
                SELECT u.user_id, u.username, u.email, u.role, u.is_active, u.created_at, u.last_login,
                       COUNT(t.record_id) as planning_years
                FROM users u
                LEFT JOIN tax_planning_years t ON u.user_id = t.user_id
                GROUP BY u.user_id
                ORDER BY u.created_at DESC
            """
            users = execute_query(users_query)
            
            if users:
                # Filter controls (Matching Reference Image 2)
                col_filter1, col_filter2, col_filter3 = st.columns(3)
                with col_filter1:
                    st.selectbox("Filter by User", ["All"] + [u['username'] for u in users], key="filter_user_dash")
                with col_filter2:
                    st.selectbox("Filter by Status", ["All", "Active", "Inactive"], key="filter_status_dash")
                with col_filter3:
                    st.selectbox("Sort by", ["User", "Created Date", "Planning Years"], key="sort_by_dash")
                
                st.caption(f"Showing {len(users)} of {len(users)} profile(s)")
                
                st.markdown("")
                
                # Display professional user profile cards
                for user in users:
                    # Status badge
                    if user['is_active']:
                        status_badge = '<span style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); color: #065f46; padding: 6px 16px; border-radius: 20px; font-size: 0.85em; font-weight: 600; border: 1px solid #10b981;">✓ ACTIVE</span>'
                    else:
                        status_badge = '<span style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); color: #7f1d1d; padding: 6px 16px; border-radius: 20px; font-size: 0.85em; font-weight: 600; border: 1px solid #ef4444;">⊘ INACTIVE</span>'
                    
                    # Action button color
                    if user['planning_years'] == 0:
                        action_color = "#94a3b8"
                        action_text = "No Plans"
                    elif user['planning_years'] > 0:
                        action_color = "#10b981"
                        action_text = f"{user['planning_years']} Plans"
                    
                    # Professional profile card
                    col_card1, col_card2 = st.columns([4, 1])
                    
                    with col_card1:
                        st.markdown(f"""
                            <div style="background: white; border-radius: 12px; padding: 24px; 
                                 border: 1px solid #e2e8f0; margin-bottom: 16px; transition: all 0.3s ease;
                                 box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                                    <h3 style="margin: 0; color: #1e293b; font-size: 1.3em;">
                                        📊 {user['username']}
                                    </h3>
                                    {status_badge}
                                </div>
                                <div style="margin: 12px 0; color: #64748b; line-height: 1.6;">
                                    <div style="margin: 6px 0;">
                                        <strong style="color: #475569;">Email:</strong> {user['email']}
                                    </div>
                                    <div style="margin: 6px 0;">
                                        <strong style="color: #475569;">Role:</strong> 
                                        <span style="text-transform: uppercase; font-weight: 600; color: {'#8b5cf6' if user['role'] == 'admin' else '#3b82f6'};">{user['role']}</span>
                                    </div>
                                    <div style="margin: 6px 0;">
                                        <strong style="color: #475569;">Planning Years:</strong> 
                                        <span style="color: {action_color}; font-weight: 600;">{action_text}</span>
                                    </div>
                                </div>
                                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #f1f5f9; font-size: 0.9em; color: #94a3b8;">
                                    <strong>Created:</strong> {user['created_at'].strftime('%Y-%m-%d') if user['created_at'] else 'N/A'} | 
                                    <strong>Last Login:</strong> {user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else 'Never'}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_card2:
                        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
                        st.button("👁️ View", key=f"view_user_{user['user_id']}", use_container_width=True)
            else:
                st.info("📭 No users found in the system")
        
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with tab2:
        st.markdown("### 👥 User Management")
        st.caption("Administrative actions and user account management")
        
        try:
            users = execute_query("SELECT * FROM users ORDER BY created_at DESC")
            
            if users:
                # Display users table
                df = pd.DataFrame(users)
                df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d')
                df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%Y-%m-%d %H:%M')
                
                st.dataframe(df[['username', 'email', 'role', 'is_active', 'created_at', 'last_login']], 
                            use_container_width=True, hide_index=True)
                
                st.divider()
                
                # User actions
                st.markdown("### ⚙️ Administrative Actions")
                
                col_action1, col_action2, col_action3 = st.columns([2, 2, 1])
                
                with col_action1:
                    selected_username = st.selectbox(
                        "Select User",
                        options=[u['username'] for u in users],
                        key="admin_user_select"
                    )
                
                with col_action2:
                    action = st.selectbox(
                        "Action",
                        ["Promote to Admin", "Demote to User", "Deactivate Account", "Activate Account"],
                        key="admin_action_select"
                    )
                
                with col_action3:
                    execute_btn = st.button("Execute", type="primary", use_container_width=True, key="admin_execute_btn")
                
                if execute_btn and selected_username:
                    selected_user = next(u for u in users if u['username'] == selected_username)
                    
                    try:
                        if action == "Promote to Admin":
                            execute_query(
                                "UPDATE users SET role = 'admin' WHERE user_id = %s",
                                (selected_user['user_id'],),
                                fetch=False
                            )
                            st.success(f"✅ {selected_username} promoted to admin")
                            st.rerun()
                        
                        elif action == "Demote to User":
                            if selected_user['user_id'] == st.session_state.user_id:
                                st.error("❌ You cannot demote yourself!")
                            else:
                                execute_query(
                                    "UPDATE users SET role = 'user' WHERE user_id = %s",
                                    (selected_user['user_id'],),
                                    fetch=False
                                )
                                st.success(f"✅ {selected_username} demoted to user")
                                st.rerun()
                        
                        elif action == "Deactivate Account":
                            if selected_user['user_id'] == st.session_state.user_id:
                                st.error("❌ You cannot deactivate yourself!")
                            else:
                                execute_query(
                                    "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                                    (selected_user['user_id'],),
                                    fetch=False
                                )
                                st.success(f"✅ {selected_username} account deactivated")
                                st.rerun()
                        
                        elif action == "Activate Account":
                            execute_query(
                                "UPDATE users SET is_active = TRUE WHERE user_id = %s",
                                (selected_user['user_id'],),
                                fetch=False
                            )
                            st.success(f"✅ {selected_username} account activated")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error executing action: {e}")
            else:
                st.info("📭 No users found")
        
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with tab3:
        st.markdown("### 📈 System Analytics Dashboard")
        st.caption("Comprehensive analytics and insights across all users and planning years")
        
        st.markdown("")
        
        # =================================================================
        # ANALYTICS FEATURE 1: User Activity Trends & Engagement Metrics
        # =================================================================
        
        st.markdown("#### 📊 User Activity Trends & Engagement Metrics")
        
        try:
            # Get user activity data
            activity_query = """
                SELECT 
                    DATE(login_time) as date,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_logins,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_logins
                FROM login_history
                WHERE login_time >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY DATE(login_time)
                ORDER BY date
            """
            activity_data = execute_query(activity_query)
            
            if activity_data and len(activity_data) > 0:
                col_act1, col_act2, col_act3 = st.columns(3)
                
                # Calculate metrics
                total_active_users = len(set([row['active_users'] for row in activity_data]))
                total_logins_30d = sum([row['total_logins'] for row in activity_data])
                avg_daily_logins = total_logins_30d / 30 if activity_data else 0
                
                with col_act1:
                    st.metric("Active Users (30d)", total_active_users, 
                             help="Unique users who logged in within last 30 days")
                
                with col_act2:
                    st.metric("Total Logins (30d)", total_logins_30d,
                             help="Total login attempts in last 30 days")
                
                with col_act3:
                    st.metric("Avg Daily Logins", f"{avg_daily_logins:.1f}",
                             help="Average logins per day over last 30 days")
                
                # Activity trend chart
                df_activity = pd.DataFrame(activity_data)
                df_activity['date'] = pd.to_datetime(df_activity['date'])
                
                activity_chart = alt.Chart(df_activity).mark_line(point=True, strokeWidth=3).encode(
                    x=alt.X('date:T', title='Date', axis=alt.Axis(format='%b %d')),
                    y=alt.Y('active_users:Q', title='Active Users'),
                    tooltip=[
                        alt.Tooltip('date:T', title='Date', format='%Y-%m-%d'),
                        alt.Tooltip('active_users:Q', title='Active Users'),
                        alt.Tooltip('total_logins:Q', title='Total Logins')
                    ]
                ).properties(
                    height=300,
                    title='Daily Active Users (Last 30 Days)'
                )
                
                st.altair_chart(activity_chart, use_container_width=True)
            else:
                st.info("📊 No activity data available yet. Activity will be tracked as users login.")
        
        except Exception as e:
            st.warning(f"Unable to load activity trends: {str(e)}")
        
        st.divider()
        
        # =================================================================
        # ANALYTICS FEATURE 2: Aggregate Portfolio Value Growth Over Time
        # =================================================================
        
        st.markdown("#### 💰 Aggregate Portfolio Value Growth Over Time")
        
        try:
            # Get portfolio growth data
            portfolio_query = """
                SELECT 
                    year,
                    SUM(COALESCE((data->>'rrsp_balance_start')::numeric, 0)) as total_rrsp,
                    SUM(COALESCE((data->>'tfsa_balance_start')::numeric, 0)) as total_tfsa,
                    SUM(
                        COALESCE((data->>'rrsp_balance_start')::numeric, 0) + 
                        COALESCE((data->>'tfsa_balance_start')::numeric, 0)
                    ) as total_aum
                FROM tax_planning_years
                GROUP BY year
                ORDER BY year
            """
            portfolio_data = execute_query(portfolio_query)
            
            if portfolio_data and len(portfolio_data) > 0:
                df_portfolio = pd.DataFrame(portfolio_data)
                
                # Summary metrics
                latest_year = df_portfolio.iloc[-1]
                total_aum = latest_year['total_aum']
                total_rrsp = latest_year['total_rrsp']
                total_tfsa = latest_year['total_tfsa']
                
                col_port1, col_port2, col_port3 = st.columns(3)
                
                with col_port1:
                    st.metric("Total AUM", f"${total_aum:,.0f}",
                             help="Total assets under management (RRSP + TFSA)")
                
                with col_port2:
                    st.metric("Total RRSP", f"${total_rrsp:,.0f}",
                             help="Combined RRSP balance across all users")
                
                with col_port3:
                    st.metric("Total TFSA", f"${total_tfsa:,.0f}",
                             help="Combined TFSA balance across all users")
                
                # Portfolio growth chart (stacked area)
                df_melted = df_portfolio.melt(
                    id_vars=['year'],
                    value_vars=['total_rrsp', 'total_tfsa'],
                    var_name='Account',
                    value_name='Balance'
                )
                
                df_melted['Account'] = df_melted['Account'].map({
                    'total_rrsp': 'RRSP',
                    'total_tfsa': 'TFSA'
                })
                
                growth_chart = alt.Chart(df_melted).mark_area(opacity=0.7).encode(
                    x=alt.X('year:O', title='Year'),
                    y=alt.Y('Balance:Q', title='Portfolio Value ($)', stack='zero'),
                    color=alt.Color('Account:N',
                        scale=alt.Scale(
                            domain=['RRSP', 'TFSA'],
                            range=['#3b82f6', '#10b981']
                        ),
                        legend=alt.Legend(title='Account Type')
                    ),
                    tooltip=[
                        alt.Tooltip('year:O', title='Year'),
                        alt.Tooltip('Account:N', title='Account'),
                        alt.Tooltip('Balance:Q', title='Balance', format='$,.0f')
                    ]
                ).properties(
                    height=300,
                    title='Portfolio Growth by Year'
                )
                
                st.altair_chart(growth_chart, use_container_width=True)
            else:
                st.info("💰 No portfolio data available yet. Data will appear as users add planning years.")
        
        except Exception as e:
            st.warning(f"Unable to load portfolio growth: {str(e)}")
        
        st.divider()
        
        # =================================================================
        # ANALYTICS FEATURE 3: Tax Optimization Success Rate Tracking
        # =================================================================
        
        st.markdown("#### 🎯 Tax Optimization Success Rate Tracking")
        
        try:
            # Get optimization stats
            optimization_query = """
                SELECT 
                    COUNT(*) as total_years,
                    SUM(CASE 
                        WHEN (
                            COALESCE((data->>'t4_gross_income')::numeric, 0) + 
                            COALESCE((data->>'other_income')::numeric, 0) -
                            COALESCE((data->>'rrsp_lump_sum_optimization')::numeric, 0) - 
                            COALESCE((data->>'rrsp_lump_sum_additional')::numeric, 0) -
                            (COALESCE((data->>'base_salary')::numeric, 0) * 
                             (COALESCE((data->>'biweekly_pct')::numeric, 0) + 
                              COALESCE((data->>'employer_match')::numeric, 0)) / 100)
                        ) < 181440 THEN 1 ELSE 0 
                    END) as optimized_years,
                    SUM(CASE 
                        WHEN (
                            COALESCE((data->>'t4_gross_income')::numeric, 0) + 
                            COALESCE((data->>'other_income')::numeric, 0)
                        ) > 0 THEN 1 ELSE 0
                    END) as years_with_data
                FROM tax_planning_years
            """
            opt_data = execute_query(optimization_query)
            
            if opt_data and opt_data[0]['total_years'] > 0:
                total = opt_data[0]['total_years']
                optimized = opt_data[0]['optimized_years']
                with_data = opt_data[0]['years_with_data']
                not_optimized = with_data - optimized
                
                success_rate = (optimized / with_data * 100) if with_data > 0 else 0
                
                col_opt1, col_opt2 = st.columns([1, 2])
                
                with col_opt1:
                    # Success rate metrics
                    st.metric("Optimization Success Rate", f"{success_rate:.1f}%",
                             help="% of planning years below $181,440 Penthouse threshold")
                    
                    st.metric("Optimized Years", f"{optimized}/{with_data}",
                             help="Years with taxable income below Penthouse threshold")
                    
                    st.metric("Need Optimization", not_optimized,
                             help="Years with Penthouse exposure",
                             delta=f"-{not_optimized} to optimize" if not_optimized > 0 else "All optimized!",
                             delta_color="inverse" if not_optimized > 0 else "normal")
                
                with col_opt2:
                    # Pie chart showing optimization breakdown
                    opt_breakdown = pd.DataFrame({
                        'Status': ['Optimized (Below $181,440)', 'Need Optimization (Above $181,440)'],
                        'Count': [optimized, not_optimized],
                        'Color': ['#10b981', '#ef4444']
                    })
                    
                    pie_chart = alt.Chart(opt_breakdown).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta('Count:Q'),
                        color=alt.Color('Status:N',
                            scale=alt.Scale(
                                domain=['Optimized (Below $181,440)', 'Need Optimization (Above $181,440)'],
                                range=['#10b981', '#ef4444']
                            ),
                            legend=alt.Legend(title='Optimization Status')
                        ),
                        tooltip=[
                            alt.Tooltip('Status:N', title='Status'),
                            alt.Tooltip('Count:Q', title='Years'),
                        ]
                    ).properties(
                        height=300,
                        title='Tax Optimization Status Distribution'
                    )
                    
                    st.altair_chart(pie_chart, use_container_width=True)
            else:
                st.info("🎯 No optimization data available yet.")
        
        except Exception as e:
            st.warning(f"Unable to load optimization stats: {str(e)}")
        
        st.divider()
        
        # =================================================================
        # ANALYTICS FEATURE 4: Average RRSP/TFSA Contribution Patterns
        # =================================================================
        
        st.markdown("#### 📈 Average RRSP/TFSA Contribution Patterns")
        
        try:
            # Get contribution patterns
            contrib_query = """
                SELECT 
                    year,
                    AVG(
                        (COALESCE((data->>'base_salary')::numeric, 0) * 
                         (COALESCE((data->>'biweekly_pct')::numeric, 0) + 
                          COALESCE((data->>'employer_match')::numeric, 0)) / 100) +
                        COALESCE((data->>'rrsp_lump_sum_optimization')::numeric, 0) +
                        COALESCE((data->>'rrsp_lump_sum_additional')::numeric, 0)
                    ) as avg_rrsp,
                    AVG(COALESCE((data->>'tfsa_lump_sum')::numeric, 0)) as avg_tfsa,
                    COUNT(*) as user_count
                FROM tax_planning_years
                WHERE COALESCE((data->>'t4_gross_income')::numeric, 0) > 0
                GROUP BY year
                ORDER BY year
            """
            contrib_data = execute_query(contrib_query)
            
            if contrib_data and len(contrib_data) > 0:
                df_contrib = pd.DataFrame(contrib_data)
                
                # Summary stats
                overall_avg_rrsp = df_contrib['avg_rrsp'].mean()
                overall_avg_tfsa = df_contrib['avg_tfsa'].mean()
                
                col_contrib1, col_contrib2, col_contrib3 = st.columns(3)
                
                with col_contrib1:
                    st.metric("Avg Annual RRSP", f"${overall_avg_rrsp:,.0f}",
                             help="Average RRSP contribution across all users")
                
                with col_contrib2:
                    st.metric("Avg Annual TFSA", f"${overall_avg_tfsa:,.0f}",
                             help="Average TFSA contribution across all users")
                
                with col_contrib3:
                    total_avg = overall_avg_rrsp + overall_avg_tfsa
                    st.metric("Avg Total Contribution", f"${total_avg:,.0f}",
                             help="Combined average RRSP + TFSA per user")
                
                # Contribution pattern chart (grouped bars)
                df_melted = df_contrib.melt(
                    id_vars=['year'],
                    value_vars=['avg_rrsp', 'avg_tfsa'],
                    var_name='Account',
                    value_name='Amount'
                )
                
                df_melted['Account'] = df_melted['Account'].map({
                    'avg_rrsp': 'Average RRSP',
                    'avg_tfsa': 'Average TFSA'
                })
                
                contrib_chart = alt.Chart(df_melted).mark_bar(opacity=0.8).encode(
                    x=alt.X('year:O', title='Year'),
                    y=alt.Y('Amount:Q', title='Average Contribution ($)'),
                    color=alt.Color('Account:N',
                        scale=alt.Scale(
                            domain=['Average RRSP', 'Average TFSA'],
                            range=['#3b82f6', '#10b981']
                        ),
                        legend=alt.Legend(title='Account Type')
                    ),
                    xOffset='Account:N',
                    tooltip=[
                        alt.Tooltip('year:O', title='Year'),
                        alt.Tooltip('Account:N', title='Account'),
                        alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                    ]
                ).properties(
                    height=300,
                    title='Average Contribution Patterns by Year'
                )
                
                st.altair_chart(contrib_chart, use_container_width=True)
            else:
                st.info("📈 No contribution data available yet.")
        
        except Exception as e:
            st.warning(f"Unable to load contribution patterns: {str(e)}")
        
        st.divider()
        
        # =================================================================
        # ANALYTICS FEATURE 5: Users Approaching Contribution Limits
        # =================================================================
        
        st.markdown("#### ⚠️ Users Approaching Contribution Limits")
        
        try:
            # Get users near limits
            limits_query = """
                SELECT 
                    u.username,
                    t.year,
                    COALESCE((t.data->>'rrsp_room')::numeric, 0) as rrsp_room,
                    COALESCE((t.data->>'tfsa_room')::numeric, 0) as tfsa_room,
                    (
                        (COALESCE((t.data->>'base_salary')::numeric, 0) * 
                         (COALESCE((t.data->>'biweekly_pct')::numeric, 0) + 
                          COALESCE((t.data->>'employer_match')::numeric, 0)) / 100) +
                        COALESCE((t.data->>'rrsp_lump_sum_optimization')::numeric, 0) +
                        COALESCE((t.data->>'rrsp_lump_sum_additional')::numeric, 0)
                    ) as rrsp_contrib,
                    COALESCE((t.data->>'tfsa_lump_sum')::numeric, 0) as tfsa_contrib
                FROM tax_planning_years t
                JOIN users u ON t.user_id = u.user_id
                WHERE COALESCE((t.data->>'rrsp_room')::numeric, 0) > 0
                   OR COALESCE((t.data->>'tfsa_room')::numeric, 0) > 0
                ORDER BY t.year DESC
            """
            limits_data = execute_query(limits_query)
            
            if limits_data and len(limits_data) > 0:
                warnings_found = 0
                
                for user_data in limits_data:
                    rrsp_room = user_data['rrsp_room']
                    tfsa_room = user_data['tfsa_room']
                    rrsp_contrib = user_data['rrsp_contrib']
                    tfsa_contrib = user_data['tfsa_contrib']
                    
                    rrsp_remaining = rrsp_room - rrsp_contrib
                    tfsa_remaining = tfsa_room - tfsa_contrib
                    
                    rrsp_util = (rrsp_contrib / rrsp_room * 100) if rrsp_room > 0 else 0
                    tfsa_util = (tfsa_contrib / tfsa_room * 100) if tfsa_room > 0 else 0
                    
                    # Show warning if >90% utilized or over limit
                    if (rrsp_util > 90 or rrsp_remaining < 0) or (tfsa_util > 90 or tfsa_remaining < 0):
                        warnings_found += 1
                        
                        warning_type = "⚠️" if rrsp_remaining >= 0 and tfsa_remaining >= 0 else "🔴"
                        
                        st.markdown(f"""
                            <div style="background: {'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)' if rrsp_remaining >= 0 and tfsa_remaining >= 0 else 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)'}; 
                                 padding: 16px; border-radius: 10px; margin-bottom: 12px; 
                                 border-left: 4px solid {'#f59e0b' if rrsp_remaining >= 0 and tfsa_remaining >= 0 else '#ef4444'};">
                                <strong>{warning_type} {user_data['username']} - {user_data['year']}</strong>
                                <div style="margin-top: 8px; font-size: 0.95em;">
                                    <strong>RRSP:</strong> ${rrsp_contrib:,.0f} / ${rrsp_room:,.0f} ({rrsp_util:.1f}% utilized) 
                                    - <span style="color: {'#059669' if rrsp_remaining >= 0 else '#dc2626'};">${abs(rrsp_remaining):,.0f} {'remaining' if rrsp_remaining >= 0 else 'OVER LIMIT'}</span><br>
                                    <strong>TFSA:</strong> ${tfsa_contrib:,.0f} / ${tfsa_room:,.0f} ({tfsa_util:.1f}% utilized) 
                                    - <span style="color: {'#059669' if tfsa_remaining >= 0 else '#dc2626'};">${abs(tfsa_remaining):,.0f} {'remaining' if tfsa_remaining >= 0 else 'OVER LIMIT'}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                
                if warnings_found == 0:
                    st.success("✅ No users approaching contribution limits. All within safe ranges!")
            else:
                st.info("⚠️ No contribution data to analyze yet.")
        
        except Exception as e:
            st.warning(f"Unable to check contribution limits: {str(e)}")
        
        st.divider()
        
        # =================================================================
        # ANALYTICS FEATURE 6: Top Optimizers Leaderboard
        # =================================================================
        
        st.markdown("#### 🏆 Top Optimizers Leaderboard")
        
        try:
            # Get top optimizers
            leaderboard_query = """
                SELECT 
                    u.username,
                    COUNT(t.record_id) as total_years,
                    SUM(CASE 
                        WHEN (
                            COALESCE((t.data->>'t4_gross_income')::numeric, 0) + 
                            COALESCE((t.data->>'other_income')::numeric, 0) -
                            COALESCE((t.data->>'rrsp_lump_sum_optimization')::numeric, 0) - 
                            COALESCE((t.data->>'rrsp_lump_sum_additional')::numeric, 0) -
                            (COALESCE((t.data->>'base_salary')::numeric, 0) * 
                             (COALESCE((t.data->>'biweekly_pct')::numeric, 0) + 
                              COALESCE((t.data->>'employer_match')::numeric, 0)) / 100)
                        ) < 181440 THEN 1 ELSE 0 
                    END) as optimized_years,
                    SUM(
                        (COALESCE((t.data->>'base_salary')::numeric, 0) * 
                         (COALESCE((t.data->>'biweekly_pct')::numeric, 0) + 
                          COALESCE((t.data->>'employer_match')::numeric, 0)) / 100) +
                        COALESCE((t.data->>'rrsp_lump_sum_optimization')::numeric, 0) +
                        COALESCE((t.data->>'rrsp_lump_sum_additional')::numeric, 0)
                    ) as total_rrsp_contrib,
                    SUM(COALESCE((t.data->>'tfsa_lump_sum')::numeric, 0)) as total_tfsa_contrib
                FROM users u
                LEFT JOIN tax_planning_years t ON u.user_id = t.user_id
                WHERE t.record_id IS NOT NULL
                GROUP BY u.username
                HAVING COUNT(t.record_id) > 0
                ORDER BY optimized_years DESC, total_rrsp_contrib DESC
                LIMIT 10
            """
            leaderboard_data = execute_query(leaderboard_query)
            
            if leaderboard_data and len(leaderboard_data) > 0:
                st.caption("Top 10 users by optimization success and contribution amounts")
                
                # Display leaderboard
                for idx, user in enumerate(leaderboard_data, 1):
                    opt_rate = (user['optimized_years'] / user['total_years'] * 100) if user['total_years'] > 0 else 0
                    total_contrib = user['total_rrsp_contrib'] + user['total_tfsa_contrib']
                    
                    # Medal emoji
                    medal = ""
                    if idx == 1:
                        medal = "🥇"
                    elif idx == 2:
                        medal = "🥈"
                    elif idx == 3:
                        medal = "🥉"
                    else:
                        medal = f"#{idx}"
                    
                    # Color based on rank
                    if idx <= 3:
                        bg_color = "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)"
                        border_color = "#f59e0b"
                    else:
                        bg_color = "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)"
                        border_color = "#3b82f6"
                    
                    st.markdown(f"""
                        <div style="background: {bg_color}; 
                             padding: 16px 20px; border-radius: 10px; margin-bottom: 10px; 
                             border-left: 4px solid {border_color}; display: flex; align-items: center;">
                            <div style="font-size: 1.5em; margin-right: 16px; min-width: 50px;">{medal}</div>
                            <div style="flex: 1;">
                                <strong style="font-size: 1.1em;">{user['username']}</strong>
                                <div style="margin-top: 4px; font-size: 0.9em;">
                                    <strong>Optimization:</strong> {user['optimized_years']}/{user['total_years']} years ({opt_rate:.1f}%) • 
                                    <strong>Total Contributions:</strong> ${total_contrib:,.0f} 
                                    (RRSP: ${user['total_rrsp_contrib']:,.0f}, TFSA: ${user['total_tfsa_contrib']:,.0f})
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("🏆 Leaderboard will populate as users create planning years.")
        
        except Exception as e:
            st.warning(f"Unable to load leaderboard: {str(e)}")
    
    # =================================================================
    # TAB 4: POWER TOOLS (Admin Only)
    # =================================================================
    
    with tab4:
        st.markdown("### ⚡ Admin Power Tools")
        st.caption("Advanced administrative functions - use with caution")
        
        st.markdown("")
        
        # TOOL 1: Login as User (Impersonation)
        st.markdown("#### 🔐 Login as User (Impersonation)")
        
        st.markdown("""
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                 padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: #1e3a8a;">Impersonate User Account</h4>
                <p style="color: #1e40af; margin-bottom: 0;">
                    Login as any user to view their account, planning years, and data. 
                    All actions will be performed as that user. Use this for support and troubleshooting.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Get all users
        all_users_query = "SELECT user_id, username, email, role FROM users ORDER BY username"
        all_users = execute_query(all_users_query)
        
        if all_users:
            col_imp1, col_imp2 = st.columns([2, 1])
            
            with col_imp1:
                user_options = [f"{u['username']} ({u['email']}) - {u['role'].upper()}" for u in all_users]
                selected_user_idx = st.selectbox(
                    "Select User to Impersonate",
                    range(len(user_options)),
                    format_func=lambda i: user_options[i],
                    key="impersonate_user_select"
                )
                
                selected_user = all_users[selected_user_idx]
            
            with col_imp2:
                st.markdown("")
                st.markdown("")
                if st.button("🔐 Login as This User", type="primary", use_container_width=True, key="impersonate_btn"):
                    # Save original admin session
                    if 'original_admin_id' not in st.session_state:
                        st.session_state.original_admin_id = st.session_state.user_id
                        st.session_state.original_admin_username = st.session_state.username
                    
                    # Switch to target user
                    st.session_state.user_id = selected_user['user_id']
                    st.session_state.username = selected_user['username']
                    st.session_state.email = selected_user['email']
                    st.session_state.role = selected_user['role']
                    st.session_state.impersonating = True
                    
                    st.success(f"✅ Now logged in as **{selected_user['username']}**")
                    st.info("👑 You are impersonating this user. Click 'Return to Admin' in sidebar to switch back.")
                    st.rerun()
        
        # Show return button if impersonating
        if st.session_state.get('impersonating', False):
            st.markdown("")
            if st.button("👑 Return to Admin Account", type="secondary", use_container_width=True, key="return_admin_btn"):
                # Restore admin session
                st.session_state.user_id = st.session_state.original_admin_id
                st.session_state.username = st.session_state.original_admin_username
                st.session_state.role = 'admin'
                st.session_state.impersonating = False
                
                # Clean up
                del st.session_state.original_admin_id
                del st.session_state.original_admin_username
                
                st.success("✅ Returned to admin account")
                st.rerun()
        
        st.divider()
        
        # TOOL 2: Reset User Data
        st.markdown("#### 🔄 Reset User Data")
        
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                 padding: 20px; border-radius: 10px; border-left: 4px solid #f59e0b; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: #78350f;">Delete All Planning Years</h4>
                <p style="color: #92400e; margin-bottom: 0;">
                    ⚠️ This will permanently delete ALL planning years for the selected user. 
                    The user account will remain, but all their financial data will be erased.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        col_reset1, col_reset2 = st.columns([2, 1])
        
        with col_reset1:
            if all_users:
                user_reset_idx = st.selectbox(
                    "Select User to Reset",
                    range(len(user_options)),
                    format_func=lambda i: user_options[i],
                    key="reset_user_select"
                )
                
                user_to_reset = all_users[user_reset_idx]
                
                # Get user's planning year count
                count_query = "SELECT COUNT(*) as count FROM tax_planning_years WHERE user_id = %s"
                count_result = execute_query(count_query, (user_to_reset['user_id'],))
                year_count = count_result[0]['count'] if count_result else 0
                
                st.caption(f"📊 This user has **{year_count}** planning years")
        
        with col_reset2:
            st.markdown("")
            st.markdown("")
            if st.button("🔄 Reset User Data", type="secondary", use_container_width=True, key="reset_user_btn"):
                if year_count > 0:
                    # Confirmation dialog
                    st.session_state.confirm_reset_user = user_to_reset['user_id']
                    st.warning(f"⚠️ **Confirm:** Delete {year_count} planning years for **{user_to_reset['username']}**?")
                else:
                    st.info("This user has no planning years to delete")
        
        # Show confirmation buttons if pending
        if st.session_state.get('confirm_reset_user'):
            col_confirm1, col_confirm2 = st.columns(2)
            
            with col_confirm1:
                if st.button("✅ YES, DELETE ALL DATA", type="primary", use_container_width=True, key="confirm_yes_reset"):
                    user_id_to_reset = st.session_state.confirm_reset_user
                    
                    # Delete user's planning years
                    execute_query(
                        "DELETE FROM tax_planning_years WHERE user_id = %s",
                        (user_id_to_reset,),
                        fetch=False
                    )
                    
                    st.success(f"✅ Successfully deleted all planning years for user")
                    del st.session_state.confirm_reset_user
                    st.rerun()
            
            with col_confirm2:
                if st.button("❌ Cancel", use_container_width=True, key="confirm_no_reset"):
                    del st.session_state.confirm_reset_user
                    st.rerun()
        
        st.divider()
        
        # TOOL 3: Nuclear Database Reset
        st.markdown("#### 💣 Nuclear Database Reset")
        
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                 padding: 20px; border-radius: 10px; border-left: 4px solid #ef4444; margin-bottom: 20px;">
                <h4 style="margin-top: 0; color: #7f1d1d;">🚨 DANGER ZONE</h4>
                <p style="color: #991b1b; margin-bottom: 0;">
                    <strong>⚠️ CRITICAL WARNING:</strong> This will permanently delete ALL data from ALL tables 
                    (except admin accounts). All users, planning years, sessions, and analytics will be erased. 
                    This action is IRREVERSIBLE.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Nuclear reset controls
        nuclear_confirm = st.checkbox("I understand this will delete ALL data", key="nuclear_checkbox")
        
        if nuclear_confirm:
            nuclear_text = st.text_input(
                "Type 'DELETE EVERYTHING' to confirm",
                key="nuclear_text_confirm"
            )
            
            if nuclear_text == "DELETE EVERYTHING":
                col_nuke1, col_nuke2 = st.columns([1, 1])
                
                with col_nuke1:
                    if st.button("💣 NUCLEAR RESET DATABASE", type="primary", use_container_width=True, key="nuclear_btn"):
                        st.session_state.nuclear_armed = True
                        st.error("⚠️ **FINAL WARNING:** Are you absolutely sure?")
                
                # Final confirmation
                if st.session_state.get('nuclear_armed', False):
                    col_final1, col_final2 = st.columns(2)
                    
                    with col_final1:
                        if st.button("🔴 YES, DELETE EVERYTHING", type="primary", use_container_width=True, key="nuclear_confirm_yes"):
                            try:
                                # Delete all data (preserve admin users)
                                execute_query("DELETE FROM tax_planning_years", fetch=False)
                                execute_query("DELETE FROM login_history", fetch=False)
                                execute_query("DELETE FROM user_sessions", fetch=False)
                                execute_query("DELETE FROM admin_audit_log", fetch=False)
                                execute_query("DELETE FROM password_reset_tokens", fetch=False)
                                execute_query("DELETE FROM email_verification_tokens", fetch=False)
                                execute_query("DELETE FROM users WHERE role != 'admin'", fetch=False)
                                
                                st.success("✅ Nuclear reset complete! All non-admin data deleted.")
                                del st.session_state.nuclear_armed
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Nuclear reset failed: {str(e)}")
                    
                    with col_final2:
                        if st.button("❌ Cancel", use_container_width=True, key="nuclear_confirm_no"):
                            del st.session_state.nuclear_armed
                            st.rerun()

# ============================================================================
# USER PROFILE PAGE
# ============================================================================

def show_profile_page():
    """Display user profile"""
    
    with st.sidebar:
        if st.button("⬅️ Back to App", use_container_width=True, key="profile_back_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="profile_logout_btn"):
            logout_user(st.session_state.session_token)
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.email = None
            st.session_state.role = None
            st.session_state.session_token = None
            st.rerun()
    
    st.title(f"👤 User Profile: {st.session_state.username}")
    
    # Account Info
    result = execute_query("SELECT * FROM users WHERE user_id = %s", (st.session_state.user_id,))
    if result:
        user = dict(result[0])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info(f"""
            **Username:** {user['username']}  
            **Email:** {user['email']}  
            **Role:** {user['role'].upper()}  
            **Created:** {user['created_at'].strftime('%B %d, %Y')}  
            **Last Login:** {user['last_login'].strftime('%B %d, %Y %I:%M %p') if user['last_login'] else 'Never'}
            """)
        
        with col2:
            st.markdown("### 📜 Recent Logins")
            history = execute_query(
                "SELECT * FROM login_history WHERE user_id = %s ORDER BY login_time DESC LIMIT 5",
                (st.session_state.user_id,)
            )
            if history:
                for entry in history:
                    status = "✅" if entry['success'] else "❌"
                    time = entry['login_time'].strftime('%m/%d %I:%M%p')
                    st.text(f"{status} {time}")
    
    # Change Password
    st.markdown("### 🔐 Change Password")
    
    with st.form("change_password_form"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password", type="primary"):
            success, message = change_password(st.session_state.user_id, 
                                              current_pw, new_pw, confirm_pw)
            
            if success:
                st.success(message)
                st.info("Logging out... Please login with your new password.")
                st.session_state.logged_in = False
                st.rerun()
            else:
                st.error(message)

# ============================================================================
# MAIN APPLICATION (from v5, with auth wrapper)
# ============================================================================

# If not logged in, show auth page
if not st.session_state.logged_in:
    show_auth_page()
    st.stop()

# If logged in, show main app
# Load user's data
all_history = load_all_data(st.session_state.user_id)

# Sidebar navigation
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    st.caption(f"Role: {st.session_state.role.upper()}")
    
    st.divider()
    
    # Admin dashboard button (only for admins)
    if st.session_state.role == 'admin':
        if st.button("👥 Admin Dashboard", use_container_width=True, key="main_admin_btn", type="primary"):
            st.session_state.current_page = "Admin"
            st.rerun()
    
    if st.button("👤 Profile Settings", use_container_width=True, key="main_profile_btn"):
        st.session_state.current_page = "Profile"
        st.rerun()
    
    if st.button("ℹ️ Version Info", use_container_width=True, key="main_version_btn"):
        st.session_state.current_page = "Version"
        st.rerun()
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary", key="main_logout_btn"):
        logout_user(st.session_state.session_token)
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.role = None
        st.session_state.session_token = None
        st.rerun()

# Show admin dashboard if selected (admin only)
if st.session_state.current_page == "Admin":
    if st.session_state.role == 'admin':
        show_admin_dashboard()
        st.stop()
    else:
        st.error("⛔ Access denied. Admin privileges required.")
        st.session_state.current_page = "Home"
        st.rerun()

# Show profile page if selected
if st.session_state.current_page == "Profile":
    show_profile_page()
    st.stop()

# Show version info page if selected
if st.session_state.current_page == "Version":
    # Version Info Page
    with st.sidebar:
        if st.button("⬅️ Back to App", use_container_width=True, key="version_back_btn"):
            st.session_state.current_page = "Home"
            st.rerun()
    
    st.title(f"ℹ️ {APP_NAME} - Version Info")
    
    # Current Version Banner
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             color: white; padding: 40px; border-radius: 16px; text-align: center; margin-bottom: 30px;
             box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);">
            <h1 style="margin: 0; font-size: 3em;">🏦</h1>
            <h2 style="margin: 20px 0 10px 0; font-size: 2em;">{APP_NAME}</h2>
            <p style="font-size: 1.2em; opacity: 0.9; margin: 0;">{APP_SUBTITLE}</p>
            <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; margin-top: 25px;">
                <p style="font-size: 1.5em; font-weight: 700; margin: 0;">{APP_VERSION}</p>
                <p style="font-size: 0.9em; margin: 5px 0 0 0; opacity: 0.9;">Released: {APP_DATE}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature Highlights
    st.markdown("## ✨ Feature Highlights")
    
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    
    with col_feat1:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
                 padding: 24px; border-radius: 12px; height: 100%; border-left: 4px solid #3b82f6;">
                <h3 style="color: #1e3a8a; margin-top: 0;">📊 Analytics</h3>
                <ul style="color: #1e40af; line-height: 1.8;">
                    <li>6 Analytics Modules</li>
                    <li>User Activity Tracking</li>
                    <li>Portfolio Growth Charts</li>
                    <li>Optimization Success Rates</li>
                    <li>Top Performers Leaderboard</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col_feat2:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                 padding: 24px; border-radius: 12px; height: 100%; border-left: 4px solid #10b981;">
                <h3 style="color: #065f46; margin-top: 0;">👑 Admin Tools</h3>
                <ul style="color: #047857; line-height: 1.8;">
                    <li>User Impersonation</li>
                    <li>Reset User Data</li>
                    <li>Nuclear Database Reset</li>
                    <li>4 Colored Metric Cards</li>
                    <li>Enhanced Management</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    with col_feat3:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                 padding: 24px; border-radius: 12px; height: 100%; border-left: 4px solid #f59e0b;">
                <h3 style="color: #78350f; margin-top: 0;">📧 Notifications</h3>
                <ul style="color: #92400e; line-height: 1.8;">
                    <li>Welcome Emails</li>
                    <li>Optimization Alerts</li>
                    <li>Deadline Reminders</li>
                    <li>Limit Warnings</li>
                    <li>SMTP Integration</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("")
    
    # Full Changelog
    st.markdown("## 📝 Complete Changelog")
    
    with st.expander("📜 View Full Version History", expanded=True):
        st.markdown(CHANGELOG)
    
    st.divider()
    
    # Technical Info
    st.markdown("## 🔧 Technical Information")
    
    col_tech1, col_tech2 = st.columns(2)
    
    with col_tech1:
        st.markdown("""
            **Platform Stack:**
            - Frontend: Streamlit
            - Database: PostgreSQL
            - Charts: Altair
            - Email: SMTP
            - Authentication: Session-based
            - Deployment: Streamlit Cloud
        """)
    
    with col_tech2:
        st.markdown("""
            **Key Features:**
            - Multi-user authentication
            - Auto-migration database
            - Real-time tax calculations
            - Multi-year planning
            - Portfolio tracking
            - Admin power tools
        """)
    
    st.divider()
    
    # Credits
    st.markdown("## 💙 Credits & Support")
    
    st.info("""
        **Built for Canadian Taxpayers**
        
        This application is designed to help Canadians optimize their RRSP and TFSA contributions,
        minimize taxes, and plan for a secure financial future.
        
        Tax rates are based on 2025/2026 Ontario (Federal + Provincial) brackets.
        Always consult with a qualified tax professional for personalized advice.
    """)
    
    st.markdown("""
        <div style="text-align: center; margin-top: 40px; padding: 30px; background: #f8fafc; border-radius: 12px;">
            <p style="font-size: 1.1em; color: #64748b; margin: 0;">
                <strong>Canadian Tax Optimizer</strong> • Built with ❤️ for Canadian taxpayers
            </p>
            <p style="font-size: 0.9em; color: #94a3b8; margin-top: 10px;">
                {APP_VERSION} • {APP_DATE}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.stop()

# Otherwise, show main app (Home or Year View)
# Continue with rest of v5 app logic...



# ============================================================================
# MAIN APPLICATION PAGES (from v5)
# ============================================================================

if st.session_state.current_page == "Home":
    st.title("🏦 TAX Optimization and TFSA Utilization")
    
    # Collapsible Help/Guide Section
    with st.expander("📖 How to Use This Dashboard", expanded=False):
        st.markdown("""
        Welcome to your comprehensive multi-year tax optimization platform. This suite helps you minimize taxes, 
        maximize RRSP/TFSA contributions, and track portfolio growth across time.
        
        **Quick Start Guide:**
        1. **Review Global Wealth Summary** - See your current portfolio value and cumulative statistics
        2. **Update Investment Snapshot** - Track your actual account balances across institutions
        3. **Check Planning Years** - Select a year to optimize that specific tax year
        4. **Analyze Trajectory** - Review your portfolio growth charts and multi-year analytics
        
        **Year Status Colors:**
        - 🟢 **Green** = Optimized (taxable income ≤ $181,440)
        - 🟠 **Orange** = In Progress (needs more RRSP contributions)
        - ⚪ **Gray** = Not Started (no data entered yet)
        """)
    
    # ===================================================================
    # QUICK STATS CARDS - NEW FEATURE
    # ===================================================================
    
    if all_history:
        st.markdown("## ⚡ Quick Stats Overview")
        st.caption("Your lifetime tax optimization and contribution summary")
        st.markdown("")
        
        # Calculate quick stats
        quick_total_rrsp = 0
        quick_total_tfsa = 0
        quick_total_tax_saved = 0
        quick_total_years = len(all_history)
        quick_optimized_years = 0
        
        for yr, data in all_history.items():
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            quick_total_rrsp += annual_rrsp
            quick_total_tfsa += tfsa_contrib
            
            refund = calculate_tax_refund(total_gross, annual_rrsp)
            quick_total_tax_saved += refund
            
            # Check if optimized
            taxable = total_gross - annual_rrsp
            if taxable < 181440:
                quick_optimized_years += 1
        
        quick_total_contrib = quick_total_rrsp + quick_total_tfsa
        quick_opt_rate = (quick_optimized_years / quick_total_years * 100) if quick_total_years > 0 else 0
        
        # Display Quick Stats Cards
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        
        with col_q1:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                     color: white; padding: 24px; border-radius: 12px; text-align: center;
                     box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">💰 Total Tax Saved</div>
                    <div style="font-size: 2.2em; font-weight: 700;">${quick_total_tax_saved:,.0f}</div>
                    <div style="font-size: 0.85em; opacity: 0.8; margin-top: 8px;">Lifetime Refunds</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_q2:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                     color: white; padding: 24px; border-radius: 12px; text-align: center;
                     box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">💼 Total Contributions</div>
                    <div style="font-size: 2.2em; font-weight: 700;">${quick_total_contrib:,.0f}</div>
                    <div style="font-size: 0.85em; opacity: 0.8; margin-top: 8px;">RRSP + TFSA Combined</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_q3:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); 
                     color: white; padding: 24px; border-radius: 12px; text-align: center;
                     box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">🎯 Optimization Rate</div>
                    <div style="font-size: 2.2em; font-weight: 700;">{quick_opt_rate:.0f}%</div>
                    <div style="font-size: 0.85em; opacity: 0.8; margin-top: 8px;">{quick_optimized_years}/{quick_total_years} Years Optimized</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col_q4:
            # Get latest portfolio value
            latest_year_key = max(all_history.keys(), key=lambda x: int(x))
            latest = all_history[latest_year_key]
            latest_cagr = latest.get("target_cagr", 7.0) / 100
            latest_rrsp_start = latest.get("rrsp_balance_start", 0)
            latest_tfsa_start = latest.get("tfsa_balance_start", 0)
            latest_rrsp_contrib = calculate_annual_rrsp(latest)
            latest_tfsa_contrib = latest.get('tfsa_lump_sum', 0)
            
            latest_rrsp_end = latest_rrsp_start * (1 + latest_cagr) + latest_rrsp_contrib * (1 + latest_cagr/2)
            latest_tfsa_end = latest_tfsa_start * (1 + latest_cagr) + latest_tfsa_contrib * (1 + latest_cagr/2)
            quick_portfolio_value = latest_rrsp_end + latest_tfsa_end
            
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
                     color: white; padding: 24px; border-radius: 12px; text-align: center;
                     box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);">
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">📊 Portfolio Value</div>
                    <div style="font-size: 2.2em; font-weight: 700;">${quick_portfolio_value:,.0f}</div>
                    <div style="font-size: 0.85em; opacity: 0.8; margin-top: 8px;">As of {latest_year_key}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("")
        st.markdown("")
        
        # ===================================================================
        # CONTRIBUTION PROGRESS BARS - NEW FEATURE
        # ===================================================================
        
        st.markdown("### 📊 Contribution Room Utilization")
        st.caption("Visual overview of your current year contribution space usage")
        st.markdown("")
        
        # Get latest year for progress bars
        if latest:
            rrsp_room = latest.get('rrsp_room', 0)
            tfsa_room = latest.get('tfsa_room', 0)
            
            rrsp_used = latest_rrsp_contrib
            tfsa_used = latest_tfsa_contrib
            
            rrsp_remaining = max(0, rrsp_room - rrsp_used)
            tfsa_remaining = max(0, tfsa_room - tfsa_used)
            
            rrsp_pct = (rrsp_used / rrsp_room * 100) if rrsp_room > 0 else 0
            tfsa_pct = (tfsa_used / tfsa_room * 100) if tfsa_room > 0 else 0
            
            # RRSP Progress Bar
            col_pb1, col_pb2 = st.columns([3, 1])
            
            with col_pb1:
                st.markdown("**RRSP Contribution Room**")
                
                # Determine color based on utilization
                if rrsp_pct >= 90:
                    rrsp_color = "#10b981"  # Green - well utilized
                elif rrsp_pct >= 60:
                    rrsp_color = "#3b82f6"  # Blue - moderate
                else:
                    rrsp_color = "#94a3b8"  # Gray - underutilized
                
                st.markdown(f"""
                    <div style="background: #f1f5f9; border-radius: 10px; padding: 3px; margin-bottom: 8px;">
                        <div style="background: {rrsp_color}; width: {min(rrsp_pct, 100):.1f}%; 
                             height: 30px; border-radius: 8px; display: flex; align-items: center; 
                             justify-content: center; color: white; font-weight: 600; font-size: 0.9em;">
                            {rrsp_pct:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"Used: ${rrsp_used:,.0f} / ${rrsp_room:,.0f} • Remaining: ${rrsp_remaining:,.0f}")
            
            with col_pb2:
                st.metric(
                    "Room Status",
                    f"{rrsp_pct:.0f}%",
                    delta=f"${rrsp_remaining:,.0f} left",
                    delta_color="inverse" if rrsp_pct < 80 else "normal"
                )
            
            st.markdown("")
            
            # TFSA Progress Bar
            col_pb3, col_pb4 = st.columns([3, 1])
            
            with col_pb3:
                st.markdown("**TFSA Contribution Room**")
                
                # Determine color based on utilization
                if tfsa_pct >= 90:
                    tfsa_color = "#10b981"  # Green - well utilized
                elif tfsa_pct >= 60:
                    tfsa_color = "#3b82f6"  # Blue - moderate
                else:
                    tfsa_color = "#94a3b8"  # Gray - underutilized
                
                st.markdown(f"""
                    <div style="background: #f1f5f9; border-radius: 10px; padding: 3px; margin-bottom: 8px;">
                        <div style="background: {tfsa_color}; width: {min(tfsa_pct, 100):.1f}%; 
                             height: 30px; border-radius: 8px; display: flex; align-items: center; 
                             justify-content: center; color: white; font-weight: 600; font-size: 0.9em;">
                            {tfsa_pct:.1f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"Used: ${tfsa_used:,.0f} / ${tfsa_room:,.0f} • Remaining: ${tfsa_remaining:,.0f}")
            
            with col_pb4:
                st.metric(
                    "Room Status",
                    f"{tfsa_pct:.0f}%",
                    delta=f"${tfsa_remaining:,.0f} left",
                    delta_color="inverse" if tfsa_pct < 80 else "normal"
                )
        
        st.divider()
    
    # SECTION 1: GLOBAL WEALTH SUMMARY (Moved to Top)
    if all_history:
        st.markdown("## 💎 Global Wealth Summary")
        
        total_rrsp_all = 0
        total_tfsa_all = 0
        total_tax_shield = 0
        total_contributions = 0
        total_investment_growth = 0
        
        # Get the latest year's ending balance
        latest_year = max(all_history.keys(), key=lambda x: int(x))
        latest_data = all_history[latest_year]
        
        for yr, data in all_history.items():
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            total_rrsp_all += annual_rrsp
            total_tfsa_all += tfsa_contrib
            total_contributions += annual_rrsp + tfsa_contrib
            
            # Calculate tax shield value
            refund = calculate_tax_refund(total_gross, annual_rrsp)
            total_tax_shield += refund
        
        # Get projected balances from latest year
        if latest_data:
            target_cagr = latest_data.get("target_cagr", 7.0) / 100
            rrsp_start = latest_data.get("rrsp_balance_start", 0)
            tfsa_start = latest_data.get("tfsa_balance_start", 0)
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(latest_data)
            tfsa_contrib = latest_data.get('tfsa_lump_sum', 0)
            
            # Calculate end of year balances (growth + new contributions)
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            latest_rrsp_balance = rrsp_start + rrsp_growth + annual_rrsp
            latest_tfsa_balance = tfsa_start + tfsa_growth + tfsa_contrib
            
            total_portfolio_value = latest_rrsp_balance + latest_tfsa_balance
            total_investment_growth = total_portfolio_value - total_contributions
        else:
            latest_rrsp_balance = 0
            latest_tfsa_balance = 0
            total_portfolio_value = 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current RRSP Balance",
                f"${latest_rrsp_balance:,.0f}",
                delta=f"${total_rrsp_all:,.0f} contributed",
                help=f"Projected RRSP value at end of {latest_year}, including all growth and contributions"
            )
        
        with col2:
            st.metric(
                "Current TFSA Balance",
                f"${latest_tfsa_balance:,.0f}",
                delta=f"${total_tfsa_all:,.0f} contributed",
                help=f"Projected TFSA value at end of {latest_year}, including all growth and contributions"
            )
        
        with col3:
            st.metric(
                "Total Tax Shield Value",
                f"${total_tax_shield:,.0f}",
                help="Cumulative tax refunds generated from all RRSP contributions across tracked years"
            )
        
        with col4:
            growth_rate_pct = (total_investment_growth / max(1, total_contributions)) * 100 if total_contributions > 0 else 0
            st.metric(
                "Total Portfolio Value",
                f"${total_portfolio_value:,.0f}",
                delta=f"+${total_investment_growth:,.0f} growth ({growth_rate_pct:.1f}%)",
                help=f"Combined RRSP + TFSA value. Growth represents investment returns above your ${total_contributions:,.0f} total contributions"
            )
        
        # Detailed explanation in expander
        with st.expander("📊 Understanding Your Global Wealth Summary", expanded=False):
            st.markdown(f"""
            This dashboard shows your complete retirement portfolio snapshot as of **December {latest_year}** (end of the most recent year you've planned):
            
            **⏰ Important Note About Tax Year Optimization:**
            When optimizing for a specific tax year (e.g., 2025), remember that **RRSP contributions can be claimed until the CRA deadline** - typically the end of February or early March of the following year. This means:
            - **Tax Year 2025** includes all RRSP contributions made from January 1, 2025 through approximately **March 1, 2026**
            - You have the first ~60 days of the new year to finalize your RRSP strategy for the previous tax year
            - Tax optimization typically happens before the end of February, giving you extra time to maximize deductions
            
            ---
            
            **💰 Current RRSP Balance: ${latest_rrsp_balance:,.0f}**
            - This is your projected RRSP account value at the end of {latest_year}
            - Includes all contributions from all years you've tracked: ${total_rrsp_all:,.0f}
            - Includes compound investment growth based on your target CAGR settings
            - This money is tax-deferred (you'll pay tax when you withdraw in retirement)
            
            **🌱 Current TFSA Balance: ${latest_tfsa_balance:,.0f}**
            - This is your projected TFSA account value at the end of {latest_year}
            - Includes all contributions from all years you've tracked: ${total_tfsa_all:,.0f}
            - Includes compound investment growth based on your target CAGR settings
            - This money grows 100% tax-free (no tax when you withdraw, ever!)
            
            **🛡️ Total Tax Shield Value: ${total_tax_shield:,.0f}**
            - This is the total amount of tax refunds you've generated through RRSP contributions
            - Every dollar you contribute to RRSP saves taxes at your marginal rate
            - Example: If you're in the 33.89% bracket, a $10,000 RRSP contribution saves $3,389 in taxes
            - This is "free money" from the government that you can reinvest (ideally into TFSA)
            
            **💎 Total Portfolio Value: ${total_portfolio_value:,.0f}**
            - This is your combined RRSP + TFSA wealth: ${latest_rrsp_balance:,.0f} + ${latest_tfsa_balance:,.0f}
            - You've contributed a total of ${total_contributions:,.0f} across all years
            - Your investments have grown by ${total_investment_growth:,.0f} ({growth_rate_pct:.1f}% return on your contributions)
            - This growth comes from compound investment returns over time
            - **Bottom line**: You put in ${total_contributions:,.0f}, and it's now worth ${total_portfolio_value:,.0f}!
            """)
        
        st.divider()
    
    # SECTION 2: INVESTMENT SNAPSHOT WORKSHEET
    st.markdown("## 📊 Investment Snapshot Worksheet")
    st.markdown("Track your actual account balances across institutions. This data is saved locally in your browser and does not affect tax calculations.")
    
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: transparent;
                padding: 10px;
            }
            
            .worksheet-container {
                max-width: 100%;
                margin: 0 auto;
            }
            
            .tables-wrapper {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 24px;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                .tables-wrapper {
                    grid-template-columns: 1fr;
                }
            }
            
            /* Match Streamlit premium-card style */
            .account-section {
                background: white;
                padding: 24px;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                border: 1px solid #e2e8f0;
                transition: all 0.3s ease;
            }
            
            .account-section:hover {
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }
            
            .account-section.rrsp {
                border-left: 4px solid #3b82f6;
            }
            
            .account-section.tfsa {
                border-left: 4px solid #10b981;
            }
            
            .section-header {
                display: flex;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 2px solid #e2e8f0;
            }
            
            .section-icon {
                font-size: 28px;
                margin-right: 12px;
            }
            
            .section-title {
                font-size: 20px;
                font-weight: 600;
                color: #1e293b;
                flex-grow: 1;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }
            
            thead {
                background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            }
            
            th {
                padding: 12px 10px;
                text-align: left;
                font-weight: 600;
                font-size: 12px;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 2px solid #cbd5e1;
            }
            
            td {
                padding: 12px 10px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            input[type="text"], input[type="number"], input[type="date"] {
                width: 100%;
                padding: 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                transition: all 0.2s ease;
                background: white;
            }
            
            input[type="text"]:hover, input[type="number"]:hover, input[type="date"]:hover {
                border-color: #94a3b8;
            }
            
            input[type="text"]:focus, input[type="number"]:focus, input[type="date"]:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            }
            
            .total-row {
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                font-weight: 600;
                border-top: 3px solid #3b82f6;
            }
            
            .total-row td {
                padding: 16px 10px;
                border-bottom: none;
            }
            
            .total-label {
                color: #1e40af;
                font-size: 15px;
                font-weight: 700;
            }
            
            .total-amount {
                color: #1e40af;
                font-size: 18px;
                font-weight: 700;
            }
            
            .btn {
                padding: 10px 18px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-right: 10px;
                font-family: inherit;
            }
            
            .btn-add {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
            }
            
            .btn-add:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
            }
            
            .btn-add:active {
                transform: translateY(0);
            }
            
            .btn-remove {
                background: #ef4444;
                color: white;
                font-size: 13px;
                padding: 6px 10px;
                border-radius: 6px;
            }
            
            .btn-remove:hover {
                background: #dc2626;
                transform: scale(1.05);
            }
            
            .actions {
                margin-top: 16px;
            }
            
            .saved-indicator {
                display: inline-flex;
                align-items: center;
                padding: 6px 14px;
                background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                color: #065f46;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                opacity: 0;
                transition: opacity 0.3s ease;
                box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
            }
            
            .saved-indicator.show {
                opacity: 1;
            }
            
            .saved-indicator::before {
                content: "✓";
                margin-right: 6px;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="worksheet-container">
            <div class="tables-wrapper">
                <!-- RRSP Section -->
                <div class="account-section rrsp">
                    <div class="section-header">
                        <span class="section-icon">💼</span>
                        <span class="section-title">RRSP Accounts</span>
                        <span class="saved-indicator" id="rrsp-saved">Saved</span>
                    </div>
                    <table id="rrsp-table">
                        <thead>
                            <tr>
                                <th style="width: 40%">Bank/Institution</th>
                                <th style="width: 30%">Balance ($)</th>
                                <th style="width: 25%">Snapshot Date</th>
                                <th style="width: 5%"></th>
                            </tr>
                        </thead>
                        <tbody id="rrsp-body">
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td class="total-label">TOTAL RRSP</td>
                                <td class="total-amount" id="rrsp-total">$0.00</td>
                                <td colspan="2"></td>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="actions">
                        <button class="btn btn-add" onclick="addRow('rrsp')">➕ Add Account</button>
                    </div>
                </div>
                
                <!-- TFSA Section -->
                <div class="account-section tfsa">
                    <div class="section-header">
                        <span class="section-icon">🌱</span>
                        <span class="section-title">TFSA Accounts</span>
                        <span class="saved-indicator" id="tfsa-saved">Saved</span>
                    </div>
                    <table id="tfsa-table">
                        <thead>
                            <tr>
                                <th style="width: 40%">Bank/Institution</th>
                                <th style="width: 30%">Balance ($)</th>
                                <th style="width: 25%">Snapshot Date</th>
                                <th style="width: 5%"></th>
                            </tr>
                        </thead>
                        <tbody id="tfsa-body">
                        </tbody>
                        <tfoot>
                            <tr class="total-row">
                                <td class="total-label">TOTAL TFSA</td>
                                <td class="total-amount" id="tfsa-total">$0.00</td>
                                <td colspan="2"></td>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="actions">
                        <button class="btn btn-add" onclick="addRow('tfsa')">➕ Add Account</button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function formatCurrency(value) {
                const num = parseFloat(value) || 0;
                return new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2
                }).format(num);
            }
            
            function calculateTotal(type) {
                const tbody = document.getElementById(`${type}-body`);
                const rows = tbody.getElementsByTagName('tr');
                let total = 0;
                
                for (let row of rows) {
                    const balanceInput = row.querySelector('.balance-input');
                    if (balanceInput) {
                        total += parseFloat(balanceInput.value) || 0;
                    }
                }
                
                document.getElementById(`${type}-total`).textContent = formatCurrency(total);
                return total;
            }
            
            function saveData(type) {
                const tbody = document.getElementById(`${type}-body`);
                const rows = tbody.getElementsByTagName('tr');
                const data = [];
                
                for (let row of rows) {
                    const bank = row.querySelector('.bank-input').value;
                    const balance = row.querySelector('.balance-input').value;
                    const date = row.querySelector('.date-input').value;
                    
                    if (bank || balance || date) {
                        data.push({ bank, balance, date });
                    }
                }
                
                localStorage.setItem(`investment-snapshot-${type}`, JSON.stringify(data));
                
                // Show saved indicator
                const indicator = document.getElementById(`${type}-saved`);
                indicator.classList.add('show');
                setTimeout(() => indicator.classList.remove('show'), 2000);
            }
            
            function loadData(type) {
                const data = JSON.parse(localStorage.getItem(`investment-snapshot-${type}`) || '[]');
                
                if (data.length === 0) {
                    addRow(type); // Add one empty row by default
                } else {
                    data.forEach(item => {
                        addRow(type, item.bank, item.balance, item.date);
                    });
                }
                
                calculateTotal(type);
            }
            
            function addRow(type, bank = '', balance = '', date = '') {
                const tbody = document.getElementById(`${type}-body`);
                const row = tbody.insertRow();
                
                row.innerHTML = `
                    <td><input type="text" class="bank-input" value="${bank}" placeholder="e.g., TD Bank, Questrade" oninput="saveData('${type}')"></td>
                    <td><input type="number" class="balance-input" value="${balance}" placeholder="0.00" step="0.01" oninput="handleBalanceChange('${type}')"></td>
                    <td><input type="date" class="date-input" value="${date}" onchange="saveData('${type}')"></td>
                    <td><button class="btn btn-remove" onclick="removeRow(this, '${type}')">✕</button></td>
                `;
            }
            
            function handleBalanceChange(type) {
                calculateTotal(type);
                saveData(type);
            }
            
            function removeRow(btn, type) {
                const row = btn.closest('tr');
                row.remove();
                calculateTotal(type);
                saveData(type);
            }
            
            // Initialize on load
            document.addEventListener('DOMContentLoaded', () => {
                loadData('rrsp');
                loadData('tfsa');
            });
        </script>
    </body>
    </html>
    """, height=520)
    
    # TFSA Information in Expander
    with st.expander("💡 Important TFSA Contribution Room Information", expanded=False):
        st.markdown("""
        **📋 Understanding CRA TFSA Contribution Room Updates:**
        
        - **Reporting Timeline:** Financial institutions must submit your prior year TFSA records to CRA by the last day of February each year. Your contribution room will be updated once this information is received and processed.
        
        - **Current Year Exclusion:** Your contribution room calculation is based on transactions made on or before December 31 of the prior year. Transactions made in the current year are NOT yet included.
        
        - **Verify Your Records:** Compare the TFSA transaction information from CRA with your own records to ensure accuracy. Use the Investment Snapshot Worksheet above to track your actual balances.
        
        - **Room May Change:** Your TFSA contribution room could change if CRA receives new or additional information from your financial institution(s).
        
        - **Excess Contributions:** Any contributions made at any time in a month over your available contribution room is an excess contribution. You will be liable to a **1% monthly tax** on your highest excess TFSA amount until you remove it.
        
        - **Non-Resident Contributions:** If you make contributions after you cease to be a resident of Canada, you may have to pay a tax on those contributions. For more information, visit [Tax payable on TFSAs - Canada.ca](https://www.canada.ca/en/revenue-agency/services/tax/individuals/topics/tax-free-savings-account/tax-payable-on-tfsas.html).
        
        ⚠️ **Pro Tip:** Always maintain your own records and compare them with CRA's information to avoid accidental over-contributions and penalties.
        """)
    
    st.divider()
    
    # SECTION 3: PLANNING YEARS
    st.markdown("## 📅 Planning Years")
    
    st.markdown("""
        <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <strong>📊 Year Status Legend:</strong>
            <span style="margin-left: 20px;">⚪ <strong>Empty</strong> - No data saved yet</span>
            <span style="margin-left: 20px;">🟠 <strong>In Progress</strong> - Has data but taxable income > $181,440 (Penthouse exposure)</span>
            <span style="margin-left: 20px;">🟢 <strong>Optimized</strong> - Fully optimized with taxable income ≤ $181,440</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Add/Remove year functionality
    st.markdown("#### ⚙️ Manage Planning Years")
    col_add1, col_add2, col_add3, col_add4 = st.columns([2, 1, 2, 1])
    
    with col_add1:
        new_year_input = st.number_input(
            "Year to Add",
            min_value=2020,
            max_value=2050,
            value=2031,
            step=1,
            key="new_year_input",
            help="Enter a year between 2020-2050 to add to your planning grid"
        )
    
    with col_add2:
        if st.button("➕ Add Year", use_container_width=True, type="primary"):
            if str(new_year_input) not in all_history:
                # Create empty year entry
                save_year_data(st.session_state.user_id, new_year_input, {
                    "t4_gross_income": 0,
                    "other_income": 0,
                    "base_salary": 0,
                    "biweekly_pct": 0,
                    "employer_match": 0,
                    "rrsp_lump_sum_optimization": 0,
                    "rrsp_lump_sum_additional": 0,
                    "tfsa_lump_sum": 0,
                    "rrsp_room": 0,
                    "tfsa_room": 0,
                    "rrsp_balance_start": 0,
                    "tfsa_balance_start": 0,
                    "target_cagr": 7.0
                })
                st.success(f"✓ Year {new_year_input} added successfully!")
                st.rerun()
            else:
                st.error(f"✗ Year {new_year_input} already exists!")
    
    with col_add3:
        if len(all_history) > 0:
            years_to_delete = [int(yr) for yr in all_history.keys()]
            delete_year_input = st.selectbox(
                "Year to Remove",
                options=sorted(years_to_delete, reverse=True),
                key="delete_year_input",
                help="Select a saved year to permanently remove from your planning"
            )
        else:
            delete_year_input = None
            st.info("💡 No saved years to remove yet")
    
    with col_add4:
        if delete_year_input and len(all_history) > 0:
            if st.button("🗑️ Remove", use_container_width=True):
                if delete_year_data(st.session_state.user_id, delete_year_input):
                    st.success(f"✓ Year {delete_year_input} removed successfully!")
                    st.rerun()
                else:
                    st.error(f"✗ Failed to remove year {delete_year_input}")
    
    st.divider()
    
    # Get all years (saved + default range)
    all_years = set(range(2024, 2031))
    all_years.update([int(yr) for yr in all_history.keys()])
    years_to_show = sorted(list(all_years))
    
    cols_per_row = 4
    
    for row_start in range(0, len(years_to_show), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, yr in enumerate(years_to_show[row_start:row_start + cols_per_row]):
            with cols[i]:
                is_saved = str(yr) in all_history
                is_optimized = is_year_optimized(all_history.get(str(yr), {})) if is_saved else False
                
                # Determine status and styling
                if not is_saved:
                    # Gray/Slate - Empty
                    status_emoji = "⚪"
                    status_text = "Empty"
                    button_label = f"📅 **{yr}**\n{status_emoji} {status_text}"
                    container_style = "background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); border: 2px solid #94a3b8; border-radius: 12px; padding: 4px;"
                elif is_optimized:
                    # Green - Optimized
                    data = all_history[str(yr)]
                    annual_rrsp = calculate_annual_rrsp(data)
                    status_emoji = "🟢"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} Optimized"
                    container_style = "background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border: 2px solid #10b981; border-radius: 12px; padding: 4px;"
                else:
                    # Orange - In Progress
                    data = all_history[str(yr)]
                    annual_rrsp = calculate_annual_rrsp(data)
                    status_emoji = "🟠"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} In Progress"
                    container_style = "background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); border: 2px solid #f97316; border-radius: 12px; padding: 4px;"
                
                # Wrap button in styled container
                st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
                
                # Create the button
                if st.button(
                    button_label,
                    key=f"home_{yr}",
                    use_container_width=True,
                    type="primary" if is_saved else "secondary"
                ):
                    st.session_state.selected_year = yr
                    st.session_state.current_page = "Year View"
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # SECTION 4: PORTFOLIO TRAJECTORY & ANALYTICS (Moved to Bottom)
    if all_history:
        st.divider()
        st.markdown("## 📈 Portfolio Growth Over Time")
        
        description_box(
            "Wealth Trajectory Visualization",
            "Track your portfolio's evolution across time. Each year shows two data points: January (start) and December (end). "
            "The stacked areas show how your RRSP (blue) and TFSA (green) accounts grow through contributions and investment returns."
        )
        
        portfolio_history = []
        
        for yr in sorted(all_history.keys(), key=lambda x: int(x)):
            data = all_history[yr]
            
            target_cagr = data.get("target_cagr", 7.0) / 100
            rrsp_start = data.get("rrsp_balance_start", 0)
            tfsa_start = data.get("tfsa_balance_start", 0)
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            # Start of year
            portfolio_history.append({
                "Year": f"{yr} (Jan)",
                "RRSP Balance": rrsp_start,
                "TFSA Balance": tfsa_start,
                "Total": rrsp_start + tfsa_start
            })
            
            # End of year (with growth and contributions)
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            rrsp_end = rrsp_start + rrsp_growth + annual_rrsp
            tfsa_end = tfsa_start + tfsa_growth + tfsa_contrib
            
            portfolio_history.append({
                "Year": f"{yr} (Dec)",
                "RRSP Balance": rrsp_end,
                "TFSA Balance": tfsa_end,
                "Total": rrsp_end + tfsa_end
            })
        
        if portfolio_history:
            df_portfolio = pd.DataFrame(portfolio_history)
            
            # Stacked area chart for portfolio composition
            portfolio_melted = df_portfolio[['Year', 'RRSP Balance', 'TFSA Balance']].melt(
                'Year',
                var_name='Account',
                value_name='Balance'
            )
            
            portfolio_chart = alt.Chart(portfolio_melted).mark_area(
                opacity=0.8,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Timeline', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Balance:Q', title='Portfolio Value ($)', stack='zero'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP Balance', 'TFSA Balance'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account Type")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Period'),
                    alt.Tooltip('Account:N', title='Account'),
                    alt.Tooltip('Balance:Q', title='Balance', format='$,.0f')
                ]
            ).properties(height=400)
            
            st.altair_chart(portfolio_chart, use_container_width=True)
            
            # Chart explanation in expander
            with st.expander("📖 How to Read Your Portfolio Growth Chart", expanded=False):
                st.markdown("""
                This stacked area chart shows how your retirement portfolio has grown over time. Here's what you're seeing:
                
                **📊 The Colored Areas:**
                - **Blue area (bottom)**: Your RRSP account balance over time
                - **Green area (top)**: Your TFSA account balance stacked on top
                - **Total height**: Your complete portfolio value (RRSP + TFSA combined)
                
                **📅 The Timeline (X-Axis):**
                - Each year appears TWICE: once for January (start of year) and once for December (end of year)
                - **January markers**: Show your portfolio value on January 1st, before making any new contributions that year
                - **December markers**: Show your portfolio value on December 31st, after all contributions and investment growth
                
                **📈 What the Growth Represents:**
                - **Vertical jumps from Jan → Dec**: This is your contributions PLUS investment returns for that year
                - **Vertical jumps from Dec → next Jan**: Usually flat (representing year rollover)
                - **Overall upward slope**: Shows your wealth-building momentum over multiple years
                
                **💡 Key Insights to Look For:**
                1. **Steeper slopes** = faster wealth accumulation (higher contributions or better returns)
                2. **Blue getting bigger** = RRSP growing (tax-deferred, good for retirement)
                3. **Green getting bigger** = TFSA growing (tax-free, good for any goal)
                4. **Consistent pattern** = disciplined, systematic saving (the best path to wealth)
                
                **🎯 Example Reading:**
                - If you see a big jump from 2025 Dec to 2026 Dec, that means you made significant contributions in 2026 AND/OR had strong investment returns
                - If the chart is mostly blue, you're focusing on tax-deferred RRSP savings
                - If the chart has more green, you're prioritizing tax-free TFSA growth
                - The ideal strategy typically uses BOTH accounts strategically
                """)
            
            # Summary stats
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            first_total = df_portfolio.iloc[0]['Total']
            last_total = df_portfolio.iloc[-1]['Total']
            total_return = last_total - first_total
            total_return_pct = (total_return / max(1, first_total)) * 100 if first_total > 0 else 0
            
            # Calculate actual time span (from first Jan to last Dec)
            first_year = int(df_portfolio.iloc[0]['Year'].split()[0])
            last_year = int(df_portfolio.iloc[-1]['Year'].split()[0])
            years_span = last_year - first_year + 1  # Include both start and end year
            
            with col_stats1:
                st.metric(
                    "Total Growth",
                    f"${total_return:,.0f}",
                    delta=f"+{total_return_pct:.1f}%",
                    help=f"Portfolio growth from {first_year} to {last_year}"
                )
            
            with col_stats2:
                # CAGR formula: ((Ending Value / Beginning Value)^(1/years)) - 1
                annualized_return = ((last_total / max(1, first_total)) ** (1 / max(1, years_span)) - 1) * 100 if first_total > 0 and years_span > 0 else 0
                st.metric(
                    "Annualized Return (CAGR)",
                    f"{annualized_return:.2f}%",
                    help=f"Compound annual growth rate over {years_span} year{'s' if years_span != 1 else ''}"
                )
            
            with col_stats3:
                st.metric(
                    "Years Tracked",
                    f"{len(all_history)}",
                    help="Number of years with saved data"
                )
        
        st.divider()
    
    # Multi-Year Analytics
    if all_history and len(all_history) > 1:
        st.markdown("## 📊 Multi-Year Analytics & Trends")
        
        description_box(
            "Comparative Analysis Dashboard",
            "Analyze patterns and trends across multiple years. The burndown charts show how efficiently you're using available contribution room. "
            "Income charts reveal your tax-shielding effectiveness. Contribution trends help you plan future savings strategies."
        )
        
        # Prepare data for charts
        chart_data = []
        room_data = []
        burndown_data = []
        
        for yr, data in sorted(all_history.items(), key=lambda x: x[0]):
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            # Use helper function for RRSP calculation
            annual_rrsp = calculate_annual_rrsp(data)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            rrsp_room_avail = data.get('rrsp_room', 0)
            tfsa_room_avail = data.get('tfsa_room', 0)
            
            chart_data.append({
                "Year": yr,
                "Gross Income": total_gross,
                "Taxable Income": total_gross - annual_rrsp,
                "Tax Shield": annual_rrsp,
                "RRSP": annual_rrsp,
                "TFSA": tfsa_contrib
            })
            
            room_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Remaining Room": max(0, rrsp_room_avail - annual_rrsp)
            })
            room_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Remaining Room": max(0, tfsa_room_avail - tfsa_contrib)
            })
            
            # Burndown data - showing used vs available
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Used",
                "Amount": annual_rrsp
            })
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Available",
                "Amount": max(0, rrsp_room_avail - annual_rrsp)
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Used",
                "Amount": tfsa_contrib
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Available",
                "Amount": max(0, tfsa_room_avail - tfsa_contrib)
            })
        
        df_chart = pd.DataFrame(chart_data)
        df_room = pd.DataFrame(room_data)
        df_burndown = pd.DataFrame(burndown_data)
        
        # RRSP & TFSA Burndown Charts
        st.markdown("### 📉 Contribution Room Burndown Analysis")
        
        col_burn1, col_burn2 = st.columns(2)
        
        with col_burn1:
            st.markdown("**RRSP Room Utilization**")
            
            rrsp_burndown = df_burndown[df_burndown['Account'] == 'RRSP']
            
            rrsp_chart = alt.Chart(rrsp_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='RRSP Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#10b981', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(rrsp_chart, use_container_width=True)
            
            # Calculate average utilization
            total_used = rrsp_burndown[rrsp_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = rrsp_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg RRSP Utilization", f"{utilization:.1f}%")
        
        with col_burn2:
            st.markdown("**TFSA Room Utilization**")
            
            tfsa_burndown = df_burndown[df_burndown['Account'] == 'TFSA']
            
            tfsa_chart = alt.Chart(tfsa_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='TFSA Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#3b82f6', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(tfsa_chart, use_container_width=True)
            
            # Calculate average utilization
            total_used = tfsa_burndown[tfsa_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = tfsa_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg TFSA Utilization", f"{utilization:.1f}%")
        
        st.divider()
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Income vs. Tax-Shielded Income**")
            
            income_df = df_chart[['Year', 'Gross Income', 'Taxable Income']].melt(
                'Year',
                var_name='Category',
                value_name='Amount'
            )
            
            income_chart = alt.Chart(income_df).mark_bar(opacity=0.85).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='Income ($)'),
                color=alt.Color('Category:N',
                    scale=alt.Scale(
                        domain=['Gross Income', 'Taxable Income'],
                        range=['#94a3b8', '#3b82f6']
                    ),
                    legend=alt.Legend(title="Income Type")
                ),
                xOffset='Category:N'
            ).properties(height=320)
            
            st.altair_chart(income_chart, use_container_width=True)
        
        with col_right:
            st.markdown("**Remaining Room Trajectory**")
            
            room_chart = alt.Chart(df_room).mark_area(
                opacity=0.7,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Remaining Room:Q', title='Remaining Room ($)'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP', 'TFSA'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account")
                )
            ).properties(height=320)
            
            st.altair_chart(room_chart, use_container_width=True)
        
        # Contribution trends
        st.markdown("### 📊 Annual Contribution Trends")
        
        contrib_df = df_chart[['Year', 'RRSP', 'TFSA']].melt(
            'Year',
            var_name='Account',
            value_name='Contribution'
        )
        
        contrib_chart = alt.Chart(contrib_df).mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white", size=80)
        ).encode(
            x=alt.X('Year:N', title='Year'),
            y=alt.Y('Contribution:Q', title='Annual Contribution ($)'),
            color=alt.Color('Account:N',
                scale=alt.Scale(
                    domain=['RRSP', 'TFSA'],
                    range=['#3b82f6', '#10b981']
                )
            ),
            strokeWidth=alt.value(3)
        ).properties(height=300)
        
        st.altair_chart(contrib_chart, use_container_width=True)
# --- 6. PAGE: YEAR VIEW ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Parameters")
        
        with st.form(key="input_form"):
            st.markdown("### 💵 Income Parameters")
            
            t4_gross_income = st.number_input(
                "Annual T4 Gross Income",
                value=float(year_data.get("t4_gross_income", 0)),
                step=5000.0,
                min_value=0.0,
                help="Total employment income from Box 14 of your T4"
            )
            
            other_income = st.number_input(
                "Other Income",
                value=float(year_data.get("other_income", 0)),
                step=1000.0,
                min_value=0.0,
                help="Additional taxable income (e.g., rental property net income after expenses)"
            )
            
            base_salary = st.number_input(
                "Annual Base Salary",
                value=float(year_data.get("base_salary", 0)),
                step=5000.0,
                min_value=0.0,
                help="Core salary used for percentage-based contributions"
            )
            
            st.caption(f"💰 Total Gross Income: ${t4_gross_income + other_income:,.0f}")
            
            st.markdown("### 🎯 RRSP Strategy")
            
            biweekly_pct = st.slider(
                "Biweekly RRSP Contribution (%)",
                0.0, 18.0,
                value=float(year_data.get("biweekly_pct", 0.0)),
                step=0.5,
                help="Percentage of base salary you contribute from each paycheck"
            )
            
            employer_match_cap = st.slider(
                "Employer Match Cap (% of Base Salary)",
                0.0, 10.0,
                value=float(year_data.get("employer_match", 4.0)),
                step=0.5,
                help="Employer matches 100% of YOUR contribution up to this % of base salary. Example: 4% cap means if you contribute 6%, employer only matches up to 4%"
            )
            
            # Calculate actual employer contribution
            employee_contribution_pct = biweekly_pct
            employer_contribution_pct = min(employee_contribution_pct, employer_match_cap)
            
            st.caption(f"💡 Your contribution: {employee_contribution_pct:.1f}% (${base_salary * employee_contribution_pct / 100:,.0f}) | "
                      f"Employer matches: {employer_contribution_pct:.1f}% (${base_salary * employer_contribution_pct / 100:,.0f})")
            
            if employee_contribution_pct > employer_match_cap:
                st.warning(f"⚠️ You're contributing {employee_contribution_pct:.1f}% but employer only matches up to {employer_match_cap:.1f}%. "
                          f"You're contributing ${base_salary * (employee_contribution_pct - employer_match_cap) / 100:,.0f} beyond the match.")
            elif employee_contribution_pct < employer_match_cap:
                missed_match = base_salary * (employer_match_cap - employee_contribution_pct) / 100
                st.info(f"💰 Opportunity: Increase contribution to {employer_match_cap:.1f}% to get ${missed_match:,.0f} more in free employer money!")
            
            rrsp_lump_sum_optimization = st.number_input(
                "RRSP Lump Sum (Tax Optimization)",
                value=float(year_data.get("rrsp_lump_sum_optimization", 0)),
                step=100.0,
                min_value=0.0,
                help="Strategic deposit to optimize tax bracket positioning"
            )
            
            rrsp_lump_sum_additional = st.number_input(
                "RRSP Lump Sum (Additional Refund)",
                value=float(year_data.get("rrsp_lump_sum_additional", 0)),
                step=100.0,
                min_value=0.0,
                help="Extra contributions to maximize tax refund beyond optimization"
            )
            
            st.caption(f"💰 Total RRSP Lump Sum: ${rrsp_lump_sum_optimization + rrsp_lump_sum_additional:,.0f}")
            
            st.markdown("### 🌱 TFSA Strategy")
            
            tfsa_lump_sum = st.number_input(
                "TFSA Lump Sum Deposit",
                value=float(year_data.get("tfsa_lump_sum", 0)),
                step=1000.0,
                min_value=0.0,
                help="Tax-free savings account contribution"
            )
            
            st.markdown("### 📋 CRA Contribution Limits")
            
            # Get default values from previous year if available
            prev_year = str(selected_year - 1)
            default_rrsp_room = 0.0
            default_tfsa_room = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Calculate remaining room from previous year using helper function
                prev_annual_rrsp = calculate_annual_rrsp(prev_data)
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                prev_rrsp_room_remaining = max(0, prev_data.get('rrsp_room', 0) - prev_annual_rrsp)
                prev_tfsa_room_remaining = max(0, prev_data.get('tfsa_room', 0) - prev_tfsa_contrib)
                
                # Add new room for current year (based on previous year's total gross income)
                prev_t4_gross = prev_data.get('t4_gross_income', 0)
                prev_other_income = prev_data.get('other_income', 0)
                prev_total_gross = prev_t4_gross + prev_other_income
                
                new_rrsp_room = min(31560, prev_total_gross * 0.18)
                new_tfsa_room = 7000
                
                default_rrsp_room = prev_rrsp_room_remaining + new_rrsp_room
                default_tfsa_room = prev_tfsa_room_remaining + new_tfsa_room
            
            rrsp_room = st.number_input(
                "Available RRSP Room",
                value=float(year_data.get("rrsp_room", default_rrsp_room)),
                step=1000.0,
                min_value=0.0,
                help="From your latest Notice of Assessment (auto-filled from previous year if available)"
            )
            
            tfsa_room = st.number_input(
                "Available TFSA Room",
                value=float(year_data.get("tfsa_room", default_tfsa_room)),
                step=1000.0,
                min_value=0.0,
                help="From CRA MyAccount (auto-filled from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_room > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} carryover + new room")
            
            st.markdown("### 📈 Portfolio Tracking")
            
            # Calculate default values from previous year's end balances
            prev_year = str(selected_year - 1)
            default_rrsp_balance = 0.0
            default_tfsa_balance = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Get previous year's values
                prev_target_cagr = prev_data.get("target_cagr", 7.0) / 100
                prev_rrsp_start = prev_data.get("rrsp_balance_start", 0)
                prev_tfsa_start = prev_data.get("tfsa_balance_start", 0)
                
                # Calculate previous year's contributions using helper function
                prev_annual_rrsp = calculate_annual_rrsp(prev_data)
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                # Calculate previous year's growth
                prev_rrsp_growth = prev_rrsp_start * prev_target_cagr + prev_annual_rrsp * (prev_target_cagr / 2)
                prev_tfsa_growth = prev_tfsa_start * prev_target_cagr + prev_tfsa_contrib * (prev_target_cagr / 2)
                
                # End balances become start balances for current year
                default_rrsp_balance = prev_rrsp_start + prev_rrsp_growth + prev_annual_rrsp
                default_tfsa_balance = prev_tfsa_start + prev_tfsa_growth + prev_tfsa_contrib
            
            rrsp_balance_start = st.number_input(
                "RRSP Balance (Start of Year)",
                value=float(year_data.get("rrsp_balance_start", default_rrsp_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total RRSP portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            tfsa_balance_start = st.number_input(
                "TFSA Balance (Start of Year)",
                value=float(year_data.get("tfsa_balance_start", default_tfsa_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total TFSA portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_balance > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} end-of-year projected balances")
            
            target_cagr = st.slider(
                "Target Annual Return (CAGR %)",
                0.0, 50.0,
                value=float(year_data.get("target_cagr", 7.0)),
                step=0.5,
                help="Expected compound annual growth rate for investments (0-50%)"
            )
            
            st.caption(f"📊 Using {target_cagr}% CAGR for growth projections")
            
            st.divider()
            
            # Form submit buttons
            col_save, col_reset = st.columns(2)
            
            with col_save:
                submitted = st.form_submit_button(
                    "💾 Save",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_reset:
                reset = st.form_submit_button(
                    "🔄 Reset",
                    use_container_width=True
                )
            
            if submitted:
                success = save_year_data(st.session_state.user_id, selected_year, {
                    "t4_gross_income": t4_gross_income,
                    "other_income": other_income,
                    "base_salary": base_salary,
                    "biweekly_pct": biweekly_pct,
                    "employer_match": employer_match_cap,
                    "rrsp_lump_sum_optimization": rrsp_lump_sum_optimization,
                    "rrsp_lump_sum_additional": rrsp_lump_sum_additional,
                    "tfsa_lump_sum": tfsa_lump_sum,
                    "rrsp_room": rrsp_room,
                    "tfsa_room": tfsa_room,
                    "rrsp_balance_start": rrsp_balance_start,
                    "tfsa_balance_start": tfsa_balance_start,
                    "target_cagr": target_cagr
                })
                
                if success:
                    st.session_state.saved_flag = True
                    st.rerun()
            
            if reset:
                delete_year_data(st.session_state.user_id, selected_year)
                st.rerun()
        
        if st.session_state.get("saved_flag"):
            st.success("✓ Strategy saved successfully!")
            st.session_state.saved_flag = False
    
    # Main content area - Calculations
    other_income = year_data.get("other_income", 0)
    total_gross_income = t4_gross_income + other_income
    
    # Calculate RRSP contributions with correct employer matching logic
    employee_rrsp_contribution = base_salary * (biweekly_pct / 100)
    employer_rrsp_contribution = base_salary * (min(biweekly_pct, employer_match_cap) / 100)
    annual_rrsp_periodic = employee_rrsp_contribution + employer_rrsp_contribution
    
    rrsp_lump_sum = rrsp_lump_sum_optimization + rrsp_lump_sum_additional
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = max(0, total_gross_income - total_rrsp_contributions)
    
    # Portfolio calculations
    rrsp_balance_start = year_data.get("rrsp_balance_start", 0)
    tfsa_balance_start = year_data.get("tfsa_balance_start", 0)
    target_cagr = year_data.get("target_cagr", 7.0) / 100  # Convert to decimal
    
    # Calculate end of year balances (growth + new contributions)
    # Assuming contributions happen throughout the year, use half-year growth on new money
    rrsp_growth_existing = rrsp_balance_start * target_cagr
    rrsp_growth_new_contrib = total_rrsp_contributions * (target_cagr / 2)  # Half year average
    rrsp_balance_end = rrsp_balance_start + rrsp_growth_existing + total_rrsp_contributions + rrsp_growth_new_contrib
    
    tfsa_growth_existing = tfsa_balance_start * target_cagr
    tfsa_growth_new_contrib = tfsa_lump_sum * (target_cagr / 2)
    tfsa_balance_end = tfsa_balance_start + tfsa_growth_existing + tfsa_lump_sum + tfsa_growth_new_contrib
    
    total_portfolio_value = rrsp_balance_end + tfsa_balance_end
    
    # Calculate tax refund
    estimated_refund = calculate_tax_refund(total_gross_income, total_rrsp_contributions)
    marginal_rate = get_marginal_rate(total_gross_income)
    
    # Optimization status
    penthouse_threshold = 181440
    
    # Check if user has started entering data
    has_started = (total_gross_income > 0 or base_salary > 0 or 
                   total_rrsp_contributions > 0 or tfsa_lump_sum > 0 or
                   rrsp_room > 0 or tfsa_room > 0)
    
    # Check if essential planning fields are complete
    # Essential fields: income source + contribution rooms
    planning_complete = ((t4_gross_income > 0 or other_income > 0) and 
                         rrsp_room > 0 and tfsa_room > 0)
    
    # Only show OPTIMIZED if planning is complete AND at or below threshold
    # Note: Income of exactly $181,440 is NOT taxed in Penthouse (due to > comparison in tax calc)
    is_optimized = planning_complete and taxable_income <= penthouse_threshold
    
    # Remaining room calculations
    remaining_rrsp_room = max(0, rrsp_room - total_rrsp_contributions)
    remaining_tfsa_room = max(0, tfsa_room - tfsa_lump_sum)
    
    # Header
    st.title(f"🏛️ Tax Optimization Strategy: {selected_year}")
    
    # Status Card
    col_status1, col_status2 = st.columns([3, 1])
    
    with col_status1:
        description_box(
            "Strategic Execution Framework",
            f"Follow this comprehensive plan to maximize your tax efficiency and wealth velocity for {selected_year}. "
            "Each section provides actionable insights to optimize your contribution strategy."
        )
    
    with col_status2:
        if is_optimized:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                     padding: 20px; border-radius: 12px; border: 2px solid #10b981; text-align: center;">
                    <div style="font-size: 3em;">🟢</div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #065f46; margin-top: 10px;">
                        OPTIMIZED
                    </div>
                    <div style="font-size: 0.9em; color: #047857; margin-top: 5px;">
                        This year will show GREEN
                    </div>
                </div>
            """, unsafe_allow_html=True)
        elif not has_started:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%); 
                     padding: 20px; border-radius: 12px; border: 2px solid #94a3b8; text-align: center;">
                    <div style="font-size: 3em;">⚪</div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #475569; margin-top: 10px;">
                        IN PLANNING
                    </div>
                    <div style="font-size: 0.9em; color: #64748b; margin-top: 5px;">
                        Enter your data to optimize
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); 
                     padding: 20px; border-radius: 12px; border: 2px solid #f97316; text-align: center;">
                    <div style="font-size: 3em;">🟠</div>
                    <div style="font-size: 1.2em; font-weight: 600; color: #7c2d12; margin-top: 10px;">
                        IN PROGRESS
                    </div>
                    <div style="font-size: 0.9em; color: #9a3412; margin-top: 5px;">
                        Complete planning to optimize
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # Key Metrics Dashboard
    st.markdown("### 📊 Strategic Overview")
    
    if other_income > 0:
        st.info(f"💼 Income Breakdown: T4 ${t4_gross_income:,.0f} + Other ${other_income:,.0f} = Total ${total_gross_income:,.0f}")
    
    # Optimization Status Banner
    if is_optimized:
        st.success(f"🟢 **OPTIMIZED** - Your taxable income (${taxable_income:,.0f}) is at or below the Penthouse threshold (${penthouse_threshold:,.0f}). This year will show GREEN on the home page.")
    else:
        deficit = taxable_income - penthouse_threshold
        additional_rrsp_needed = deficit
        st.warning(f"🟠 **IN PROGRESS** - Your taxable income (${taxable_income:,.0f}) exceeds the Penthouse threshold by ${deficit:,.0f}. "
                  f"Add ${additional_rrsp_needed:,.0f} more to RRSP contributions to achieve GREEN optimization status and save ${deficit * 0.4797:,.0f} in taxes.")
        
        # Pending Items Checklist
        st.markdown("### ✅ Pending Items to Reach Optimization")
        
        pending_items = []
        
        # Item 1: RRSP contribution needed
        if deficit > 0:
            pending_items.append({
                "item": "Increase RRSP Contributions",
                "current": f"${total_rrsp_contributions:,.0f}",
                "target": f"${total_rrsp_contributions + deficit:,.0f}",
                "action": f"Add ${deficit:,.0f} to either 'RRSP Lump Sum (Tax Optimization)' or 'RRSP Lump Sum (Additional Refund)' in the sidebar",
                "impact": f"Saves ${deficit * 0.4797:,.0f} in taxes at 47.97% Penthouse rate"
            })
        
        # Item 2: Room availability check
        if deficit > remaining_rrsp_room:
            pending_items.append({
                "item": "⚠️ Insufficient RRSP Room",
                "current": f"${remaining_rrsp_room:,.0f} available",
                "target": f"${deficit:,.0f} needed",
                "action": f"You need ${deficit - remaining_rrsp_room:,.0f} more RRSP room than available. Consider: (1) Verify your NOA room is correct, (2) Use spousal RRSP if married, (3) Accept partial optimization this year",
                "impact": "May not achieve full green status this year"
            })
        
        if pending_items:
            for idx, item in enumerate(pending_items, 1):
                st.markdown(f"""
                    <div class="premium-card" style="border-left: 4px solid #f59e0b;">
                        <h4>Item {idx}: {item['item']}</h4>
                        <p><strong>Current:</strong> {item['current']} | <strong>Target:</strong> {item['target']}</p>
                        <p><strong>Action Required:</strong> {item['action']}</p>
                        <p style="color: #059669;"><strong>Impact:</strong> {item['impact']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No pending items - year is optimized!")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Gross Income",
            f"${total_gross_income:,.0f}",
            delta=f"+${other_income:,.0f} other" if other_income > 0 else None,
            help="T4 employment income plus other taxable income"
        )
    
    with col2:
        st.metric(
            "Taxable Income",
            f"${taxable_income:,.0f}",
            delta=f"-${total_rrsp_contributions:,.0f}",
            delta_color="inverse",
            help="Income after RRSP deductions"
        )
    
    with col3:
        st.metric(
            "Marginal Tax Rate",
            f"{marginal_rate*100:.2f}%",
            help="Your current tax bracket rate"
        )
    
    with col4:
        st.metric(
            "Estimated Tax Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}% ROI",
            help="Tax refund from RRSP contributions"
        )
    
    with col5:
        st.metric(
            "Total Portfolio Value",
            f"${total_portfolio_value:,.0f}",
            delta=f"+{target_cagr*100:.1f}% target",
            help="Combined RRSP + TFSA projected end-of-year value"
        )
    
    # Portfolio Growth Dashboard
    if rrsp_balance_start > 0 or tfsa_balance_start > 0 or annual_rrsp_periodic > 0:
        st.divider()
        st.markdown("### 💼 Portfolio Growth Tracker")
        
        # Show RRSP contribution breakdown
        if annual_rrsp_periodic > 0:
            st.markdown("#### 🎯 RRSP Contribution Breakdown")
            col_breakdown1, col_breakdown2, col_breakdown3 = st.columns(3)
            
            with col_breakdown1:
                st.metric(
                    "Your Paycheck Contributions",
                    f"${employee_rrsp_contribution:,.0f}",
                    delta=f"{biweekly_pct:.1f}% of base salary",
                    help="Amount deducted from your paychecks throughout the year"
                )
            
            with col_breakdown2:
                st.metric(
                    "Employer Match",
                    f"${employer_rrsp_contribution:,.0f}",
                    delta=f"{min(biweekly_pct, employer_match_cap):.1f}% matched",
                    help=f"Free money! Employer matches 100% up to {employer_match_cap:.1f}% cap"
                )
            
            with col_breakdown3:
                st.metric(
                    "Total Periodic RRSP",
                    f"${annual_rrsp_periodic:,.0f}",
                    delta=f"${employer_rrsp_contribution:,.0f} is FREE",
                    help="Combined employee + employer contributions from paychecks"
                )
            
            st.divider()
        
        description_box(
            "Year-End Portfolio Projection",
            f"Based on {target_cagr*100:.1f}% annual return assumption. Growth calculated on existing balance (full year) and new contributions (half year average)."
        )
        
        # Create portfolio table
        portfolio_table_data = []
        
        # RRSP Row
        portfolio_table_data.append({
            "Account": "RRSP",
            "Start Balance": f"${rrsp_balance_start:,.0f}",
            "New Contributions": f"${total_rrsp_contributions:,.0f}",
            "Investment Growth": f"${rrsp_growth_existing + rrsp_growth_new_contrib:,.0f}",
            "End Balance": f"${rrsp_balance_end:,.0f}",
            "Net Gain": f"${rrsp_balance_end - rrsp_balance_start:,.0f}"
        })
        
        # TFSA Row
        portfolio_table_data.append({
            "Account": "TFSA",
            "Start Balance": f"${tfsa_balance_start:,.0f}",
            "New Contributions": f"${tfsa_lump_sum:,.0f}",
            "Investment Growth": f"${tfsa_growth_existing + tfsa_growth_new_contrib:,.0f}",
            "End Balance": f"${tfsa_balance_end:,.0f}",
            "Net Gain": f"${tfsa_balance_end - tfsa_balance_start:,.0f}"
        })
        
        # Total Row
        total_start = rrsp_balance_start + tfsa_balance_start
        total_contributions = total_rrsp_contributions + tfsa_lump_sum
        total_growth = (rrsp_growth_existing + rrsp_growth_new_contrib + 
                      tfsa_growth_existing + tfsa_growth_new_contrib)
        
        portfolio_table_data.append({
            "Account": "**TOTAL**",
            "Start Balance": f"**${total_start:,.0f}**",
            "New Contributions": f"**${total_contributions:,.0f}**",
            "Investment Growth": f"**${total_growth:,.0f}**",
            "End Balance": f"**${total_portfolio_value:,.0f}**",
            "Net Gain": f"**${total_portfolio_value - total_start:,.0f}**"
        })
        
        df_portfolio = pd.DataFrame(portfolio_table_data)
        
        st.dataframe(
            df_portfolio,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Account": st.column_config.TextColumn("Account", width="small"),
                "Start Balance": st.column_config.TextColumn("Start of Year", width="medium"),
                "New Contributions": st.column_config.TextColumn("Contributions", width="medium"),
                "Investment Growth": st.column_config.TextColumn(f"Growth @ {target_cagr*100:.1f}%", width="medium"),
                "End Balance": st.column_config.TextColumn("Projected End", width="medium"),
                "Net Gain": st.column_config.TextColumn("Total Gain", width="medium")
            }
        )
        
        # Quick insights
        col_insight1, col_insight2, col_insight3 = st.columns(3)
        
        with col_insight1:
            growth_rate_actual = ((total_growth / max(1, total_start)) * 100) if total_start > 0 else 0
            st.metric("Portfolio Growth Rate", f"{growth_rate_actual:.2f}%", 
                     help="Actual growth rate on starting balance")
        
        with col_insight2:
            contribution_impact = ((total_contributions / max(1, total_portfolio_value)) * 100)
            st.metric("Contribution Impact", f"{contribution_impact:.1f}%",
                     help="% of end value from new contributions")
        
        with col_insight3:
            investment_impact = ((total_growth / max(1, total_portfolio_value)) * 100)
            st.metric("Investment Impact", f"{investment_impact:.1f}%",
                     help="% of end value from market growth")
    
    st.divider()
    
    # Tax Building Visualizer
    st.markdown("### 🏢 Tax Building Visualizer")
    
    description_box(
        "Income Distribution Across Tax Brackets",
        "This chart shows how your income is distributed across tax floors. "
        "Blue bars represent tax-shielded income (protected by RRSP), "
        "while orange bars show taxable income. Your goal: maximize the blue."
    )
    
    # Build the tax building data
    building_data = []
    
    for bracket in TAX_BRACKETS:
        # Total income in this bracket
        total_in_bracket = min(total_gross_income, bracket['high']) - bracket['low']
        
        if total_in_bracket <= 0:
            continue
        
        # Taxable amount in this bracket
        taxed_amt = max(0, min(bracket['high'], taxable_income) - bracket['low'])
        
        # Shielded amount in this bracket
        shielded_amt = total_in_bracket - taxed_amt
        
        if shielded_amt > 0:
            building_data.append({
                "Floor": bracket['name'],
                "Amount": shielded_amt,
                "Status": "Tax-Shielded",
                "Rate": f"{bracket['rate']*100:.2f}%"
            })
        
        if taxed_amt > 0:
            building_data.append({
                "Floor": bracket['name'],
                "Amount": taxed_amt,
                "Status": "Taxable",
                "Rate": f"{bracket['rate']*100:.2f}%"
            })
    
    if building_data:
        df_building = pd.DataFrame(building_data)
        
        # Create ordered floor list for proper sorting
        floor_order = [b['name'] for b in TAX_BRACKETS]
        
        building_chart = alt.Chart(df_building).mark_bar().encode(
            x=alt.X('Floor:N',
                title='Tax Bracket Floor',
                sort=floor_order
            ),
            y=alt.Y('Amount:Q',
                title='Income Amount ($)',
                stack='zero'
            ),
            color=alt.Color('Status:N',
                scale=alt.Scale(
                    domain=['Tax-Shielded', 'Taxable'],
                    range=['#3b82f6', '#f59e0b']
                ),
                legend=alt.Legend(title="Status", orient="top")
            ),
            tooltip=[
                alt.Tooltip('Floor:N', title='Bracket'),
                alt.Tooltip('Status:N', title='Status'),
                alt.Tooltip('Amount:Q', title='Amount', format='$,.0f'),
                alt.Tooltip('Rate:N', title='Tax Rate')
            ]
        ).properties(
            height=400
        )
        
        st.altair_chart(building_chart, use_container_width=True)
    else:
        st.info("Enter your income parameters in the sidebar to see the tax building visualization.")
    
    st.divider()
    
    # Strategic Prioritization
    st.markdown("### 🎯 Strategic Prioritization Matrix")
    
    description_box(
        "Optimization Roadmap",
        f"**Goal**: Reduce taxable income to or below ${penthouse_threshold:,.0f} to avoid the Penthouse bracket (47.97% tax rate). "
        f"Current status: {'✅ Optimized' if is_optimized else '⚠️ Needs Optimization'}"
    )
    
    # Calculate optimization metrics
    penthouse_income = max(0, taxable_income - penthouse_threshold)
    penthouse_shield_needed = max(0, total_gross_income - penthouse_threshold - total_rrsp_contributions)
    
    # Priority 1: Penthouse Shield
    if penthouse_income > 0:
        priority_1_status = f"⚠️ ${penthouse_income:,.0f} in Penthouse"
        priority_1_action = f"Increase RRSP by ${penthouse_shield_needed:,.0f}"
        priority_1_impact = f"Save ${penthouse_income * 0.4797:,.0f} in taxes (47.97% rate)"
        priority_1_class = "priority-high"
        
        # Show progress bar
        optimization_progress = min(1.0, (penthouse_threshold / max(1, taxable_income)))
        st.markdown("**Optimization Progress:**")
        st.progress(optimization_progress)
        st.caption(f"{optimization_progress*100:.1f}% optimized - Need to reduce taxable income by ${penthouse_income:,.0f}")
    else:
        priority_1_status = "✅ Optimized"
        priority_1_action = "No Penthouse exposure"
        priority_1_impact = f"Maximum efficiency at {marginal_rate*100:.2f}% bracket"
        priority_1_class = "priority-medium"
        
        st.markdown("**Optimization Progress:**")
        st.progress(1.0)
        st.caption("✅ 100% optimized - Below Penthouse threshold!")
    
    st.markdown(f'''
        <div class="premium-card {priority_1_class}">
            <h4>Priority 1: High-Rate Tax Shield</h4>
            <p><strong>Status:</strong> {priority_1_status}</p>
            <p><strong>Action:</strong> {priority_1_action}</p>
            <p><strong>Impact:</strong> {priority_1_impact}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Priority 2: TFSA Maximization
    st.markdown(f'''
        <div class="premium-card priority-medium">
            <h4>Priority 2: Tax-Free Growth Acceleration</h4>
            <p><strong>Status:</strong> ${remaining_tfsa_room:,.0f} TFSA room remaining</p>
            <p><strong>Action:</strong> Maximize TFSA contributions for tax-free compounding</p>
            <p><strong>Impact:</strong> All future gains grow tax-free forever</p>
        </div>
    ''', unsafe_allow_html=True)
    
    st.divider()
    
    # THE FEEDBACK LOOP - Tax Refund Reinvestment
    st.markdown("### 🔄 The Feedback Loop: Refund Reinvestment")
    
    description_box(
        "Strategic Refund Deployment",
        f"Your RRSP contributions of ${total_rrsp_contributions:,.0f} will generate an estimated tax refund of ${estimated_refund:,.0f}. "
        "Deploy this refund strategically into your TFSA to accelerate tax-free wealth growth."
    )
    
    col_refund1, col_refund2, col_refund3 = st.columns(3)
    
    with col_refund1:
        st.metric(
            "Tax Refund Generated",
            f"${estimated_refund:,.0f}",
            help="Estimated refund from RRSP tax deductions"
        )
    
    with col_refund2:
        available_for_tfsa = min(estimated_refund, remaining_tfsa_room)
        st.metric(
            "Available for TFSA",
            f"${available_for_tfsa:,.0f}",
            help="Refund amount that fits in remaining TFSA room"
        )
    
    with col_refund3:
        reinvest_pct = (available_for_tfsa / max(1, estimated_refund)) * 100
        st.metric(
            "Reinvestment Rate",
            f"{reinvest_pct:.1f}%",
            help="Percentage of refund deployable to TFSA"
        )
    
    # Refund deployment calculator
    with st.expander("🧮 Refund Deployment Calculator", expanded=True):
        st.markdown("**Strategic Question:** How much of your tax refund will you reinvest into your TFSA?")
        
        if estimated_refund > 0:
            refund_to_deploy = st.slider(
                "Amount to reinvest in TFSA",
                0.0,
                float(estimated_refund),
                value=min(float(estimated_refund), float(remaining_tfsa_room)),
                step=100.0
            )
            
            st.caption(f"Selected amount: ${refund_to_deploy:,.0f}")
            
            col_deploy1, col_deploy2 = st.columns(2)
            
            with col_deploy1:
                st.markdown("**Deployment Impact:**")
                new_tfsa_total = tfsa_lump_sum + refund_to_deploy
                new_tfsa_room = max(0, tfsa_room - new_tfsa_total)
                
                st.write(f"- Total TFSA contribution: ${new_tfsa_total:,.0f}")
                st.write(f"- Remaining TFSA room: ${new_tfsa_room:,.0f}")
                st.write(f"- Combined tax-advantaged savings: ${total_rrsp_contributions + new_tfsa_total:,.0f}")
            
            with col_deploy2:
                st.markdown("**20-Year Growth Projection:**")
                # Assuming 7% annual return
                growth_rate = 0.07
                years = 20
                future_value = refund_to_deploy * ((1 + growth_rate) ** years)
                tax_saved_at_withdrawal = future_value * marginal_rate
                
                st.write(f"- Refund deployed: ${refund_to_deploy:,.0f}")
                st.write(f"- Future value @ 7%: ${future_value:,.0f}")
                st.write(f"- Tax saved (vs. taxable): ${tax_saved_at_withdrawal:,.0f}")
        else:
            st.info("💡 Make RRSP contributions to generate a tax refund that can be reinvested into your TFSA for tax-free growth.")
    
    st.divider()
    
    # March 1st Deadline Dashboard
    st.markdown(f"### 📅 March 1st Deadline Dashboard ({selected_year + 1})")
    
    col_deadline = st.columns([3, 1])
    with col_deadline[1]:
        components.html('''
            <button onclick="window.print()" 
                style="width: 100%; height: 60px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                color: white; border: none; border-radius: 10px; font-weight: 600; 
                cursor: pointer; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4);
                transition: all 0.3s ease;">
                📄 Save as PDF
            </button>
        ''', height=80)
    
    st.markdown(f"""
        <div class="premium-card">
            <h4>Critical Action Items Before March 1, {selected_year + 1}</h4>
            <p style="color: #64748b; margin-bottom: 20px;">
                These deposits must be completed to claim deductions for tax year {selected_year}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    ac1, ac2, ac3, ac4, ac5 = st.columns(5)
    
    with ac1:
        st.metric(
            "RRSP Optimization",
            f"${rrsp_lump_sum_optimization:,.0f}",
            help="Strategic deposit for tax bracket optimization"
        )
    
    with ac2:
        st.metric(
            "RRSP Additional",
            f"${rrsp_lump_sum_additional:,.0f}",
            help="Extra contributions for maximum refund"
        )
    
    with ac3:
        st.metric(
            "TFSA Deposit",
            f"${tfsa_lump_sum:,.0f}",
            help="Tax-free savings contribution"
        )
    
    with ac4:
        st.metric(
            "Expected Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}%",
            help="Tax refund from all RRSP contributions"
        )
    
    with ac5:
        net_cashflow = estimated_refund - rrsp_lump_sum - tfsa_lump_sum
        st.metric(
            "Net Cashflow Impact",
            f"${net_cashflow:,.0f}",
            delta="Surplus" if net_cashflow >= 0 else "Investment",
            delta_color="normal" if net_cashflow >= 0 else "inverse",
            help="Refund minus deposits"
        )
    
    st.divider()
    
    # Carryover Room Projection
    st.markdown(f"### ⏭️ {selected_year + 1} Carryover Room Projection")
    
    description_box(
        "Forward-Looking Planning",
        f"Based on CRA's indexed limits and your {selected_year} contributions, "
        "here's your projected contribution room for next year."
    )
    
    # RRSP new room calculation (18% of income, max $31,560 for 2025)
    rrsp_earned_room = min(31560, total_gross_income * 0.18)
    projected_rrsp_room = remaining_rrsp_room + rrsp_earned_room
    
    # TFSA new room (indexed amount, $7,000 for 2025)
    tfsa_earned_room = 7000
    projected_tfsa_room = remaining_tfsa_room + tfsa_earned_room
    
    col_carry1, col_carry2 = st.columns(2)
    
    with col_carry1:
        st.markdown("**RRSP Room Evolution**")
        st.metric(
            f"{selected_year + 1} Projected RRSP Room",
            f"${projected_rrsp_room:,.0f}",
            delta=f"+${rrsp_earned_room:,.0f} new",
            help="Unused room + newly earned contribution room"
        )
        
        st.progress(min(1.0, total_rrsp_contributions / max(1, rrsp_room)))
        st.caption(f"You used {(total_rrsp_contributions/max(1,rrsp_room))*100:.1f}% of available RRSP room in {selected_year}")
    
    with col_carry2:
        st.markdown("**TFSA Room Evolution**")
        st.metric(
            f"{selected_year + 1} Projected TFSA Room",
            f"${projected_tfsa_room:,.0f}",
            delta=f"+${tfsa_earned_room:,.0f} new",
            help="Unused room + annual indexed increase"
        )
        
        st.progress(min(1.0, tfsa_lump_sum / max(1, tfsa_room)))
        st.caption(f"You used {(tfsa_lump_sum/max(1,tfsa_room))*100:.1f}% of available TFSA room in {selected_year}")
    
    st.divider()
    
    # Tax Bracket Reference
    st.markdown("### 📑 Ontario Tax Bracket Reference (Combined Federal + Provincial)")
    
    with st.expander("📊 View Detailed Bracket Information", expanded=False):
        description_box(
            "2025/2026 Marginal Tax Rates",
            "These are the combined federal and Ontario provincial marginal tax rates. "
            "Your marginal rate is the tax you pay on each additional dollar earned."
        )
        
        bracket_df = pd.DataFrame([
            {
                "Floor Level": bracket['name'],
                "Income Range": f"${bracket['low']:,} - ${bracket['high']:,}" if bracket['high'] != float('inf') else f"${bracket['low']:,}+",
                "Marginal Rate": f"{bracket['rate']*100:.2f}%",
                "Tax on $1,000": f"${1000 * bracket['rate']:.2f}"
            }
            for bracket in TAX_BRACKETS
        ])
        
        st.dataframe(
            bracket_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Highlight current bracket
        current_bracket = None
        for bracket in TAX_BRACKETS:
            if bracket['low'] <= taxable_income < bracket['high']:
                current_bracket = bracket
                break
        
        if current_bracket and taxable_income > 0:
            st.info(f"📍 Your current marginal bracket: **{current_bracket['name']}** at **{current_bracket['rate']*100:.2f}%**")
    
    # Strategic Insights
    st.divider()
    st.markdown("### 💡 Strategic Insights & Recommendations")
    
    insights = []
    
    # Insight 1: Penthouse exposure
    if penthouse_income > 0:
        insights.append({
            "icon": "⚠️",
            "title": "High Priority: Penthouse Exposure",
            "message": f"You have ${penthouse_income:,.0f} exposed to the Penthouse rate (47.97%). "
                      f"Consider depositing an additional ${penthouse_shield_needed:,.0f} to your RRSP before March 1st "
                      f"to save ${penthouse_income * 0.4797:,.0f} in taxes.",
            "priority": "high"
        })
    
    # Insight 2: Unused RRSP room
    if remaining_rrsp_room > 10000:
        insights.append({
            "icon": "💰",
            "title": "Opportunity: Unused RRSP Room",
            "message": f"You have ${remaining_rrsp_room:,.0f} of unused RRSP room. "
                      f"At your marginal rate of {marginal_rate*100:.2f}%, every additional $10,000 contributed "
                      f"would generate a ${10000 * marginal_rate:,.0f} tax refund.",
            "priority": "medium"
        })
    
    # Insight 3: TFSA optimization
    if remaining_tfsa_room > 5000:
        insights.append({
            "icon": "🌱",
            "title": "Growth Opportunity: TFSA Capacity",
            "message": f"You have ${remaining_tfsa_room:,.0f} of unused TFSA room. "
                      f"Consider deploying your ${estimated_refund:,.0f} tax refund into this tax-free growth vehicle. "
                      f"Over 20 years at 7% annual returns, this could grow to ${estimated_refund * (1.07**20):,.0f} tax-free.",
            "priority": "medium"
        })
    
    # Insight 4: Employer match
    if employer_match_cap > 0:
        employer_contribution = base_salary * (min(biweekly_pct, employer_match_cap) / 100)
        employee_contribution = base_salary * (biweekly_pct / 100)
        
        if employee_contribution > 0:
            if biweekly_pct >= employer_match_cap:
                # Maximizing match - SUCCESS (Green)
                insights.append({
                    "icon": "✅",
                    "title": "Excellent: Maximizing Employer Match",
                    "message": f"You're contributing {biweekly_pct:.1f}% (${employee_contribution:,.0f}) and your employer is matching "
                              f"{employer_match_cap:.1f}% (${employer_contribution:,.0f}). You're getting the full match! "
                              f"This is ${employer_contribution:,.0f} of free money every year. Keep it up!",
                    "priority": "success"
                })
            else:
                # Not maximizing match
                missed_match = base_salary * (employer_match_cap - biweekly_pct) / 100
                insights.append({
                    "icon": "⚠️",
                    "title": "Opportunity: Not Maximizing Employer Match",
                    "message": f"You're contributing {biweekly_pct:.1f}% (${employee_contribution:,.0f}) but your employer will match up to "
                              f"{employer_match_cap:.1f}%. You're currently getting ${employer_contribution:,.0f} in employer match, "
                              f"but you're leaving ${missed_match:,.0f} of FREE MONEY on the table. "
                              f"Increase your contribution to {employer_match_cap:.1f}% to capture the full match.",
                    "priority": "high"
                })
        else:
            # Not contributing at all
            potential_match = base_salary * (employer_match_cap / 100)
            insights.append({
                "icon": "🚨",
                "title": "Critical: Missing 100% of Employer Match",
                "message": f"Your employer offers to match up to {employer_match_cap:.1f}% of your base salary (${potential_match:,.0f} per year). "
                          f"You're currently contributing 0%, so you're leaving ALL of this free money on the table. "
                          f"This is a guaranteed 100% return on your contribution up to {employer_match_cap:.1f}%. Start contributing immediately!",
                "priority": "high"
            })
    
    # Insight 5: Efficiency score
    efficiency_score = (total_rrsp_contributions / max(1, rrsp_room)) * 0.5 + \
                      (tfsa_lump_sum / max(1, tfsa_room)) * 0.5
    
    if efficiency_score < 0.5:
        insights.append({
            "icon": "📈",
            "title": "Efficiency Opportunity",
            "message": f"Your contribution room utilization is {efficiency_score*100:.1f}%. "
                      f"You're leaving significant tax advantages on the table. "
                      f"Consider increasing your automatic contributions or making larger lump-sum deposits.",
            "priority": "medium"
        })
    elif efficiency_score > 0.8:
        insights.append({
            "icon": "✨",
            "title": "Excellent Optimization",
            "message": f"Your contribution room utilization is {efficiency_score*100:.1f}%. "
                      f"You're making excellent use of your available tax-advantaged space. "
                      f"Keep up this disciplined approach to wealth building!",
            "priority": "success"
        })
    
    # Display insights
    for insight in insights:
        if insight['priority'] == "high":
            priority_class = "priority-high"
        elif insight['priority'] == "success":
            priority_class = "priority-success"
        else:
            priority_class = "priority-medium"
        
        st.markdown(f'''
            <div class="premium-card {priority_class}">
                <h4>{insight['icon']} {insight['title']}</h4>
                <p style="line-height: 1.6;">{insight['message']}</p>
            </div>
        ''', unsafe_allow_html=True)
    
    if not insights:
        st.success("✅ Your strategy is well-optimized! No critical action items identified.")

# Footer
st.divider()
current_date = datetime.now().strftime("%B %d, %Y")
st.markdown(f"""
    <div style="text-align: center; color: #64748b; padding: 20px;">
        <p><strong>TAX Optimization and TFSA Utilization</strong></p>
        <p style="font-size: 0.9em;">
            Tax rates are based on 2025/2026 Ontario combined federal + provincial brackets. 
            Always consult with a qualified tax professional for personalized advice.
        </p>
        <p style="font-size: 0.85em; margin-top: 10px;">
            RRSP contribution limit: 18% of previous year's income (max $31,560) | 
            TFSA annual limit: $7,000
        </p>
        <p style="font-size: 0.75em; margin-top: 15px; color: #94a3b8;">
            Version {APP_VERSION} • {APP_DATE} • Generated on {current_date}
        </p>
    </div>
""", unsafe_allow_html=True)
