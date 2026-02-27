import os
import random
import hashlib
from datetime import datetime, timedelta

import psycopg2
import streamlit as st
import yagmail
from dotenv import load_dotenv

from db.db import get_connection

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RESET_OTP_EXPIRY_MINUTES = int(os.getenv("RESET_OTP_EXPIRY_MINUTES", "10"))


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_auth_tables():
    """Initialize users table if it doesn't exist"""
    try:
        conn = get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create index on username for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        ''')
        
        # Create index on email
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                otp VARCHAR(10) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_password_reset_user ON password_reset_tokens(user_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_password_reset_expires ON password_reset_tokens(expires_at)
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Auth tables initialized successfully")
        return True
        
    except Exception as e:
        print(f"Error initializing auth tables: {e}")
        return False


def verify_user(username: str, password: str) -> dict:
    """Verify user credentials"""
    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}
        
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        cursor.execute('''
            SELECT id, username, email, full_name, is_active
            FROM users
            WHERE username = %s AND password_hash = %s
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and user[4]:  # user exists and is_active
            return {
                "success": True,
                "user": {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "full_name": user[3]
                }
            }
        elif user and not user[4]:
            return {"success": False, "message": "Account is deactivated"}
        else:
            return {"success": False, "message": "Invalid username or password"}
            
    except Exception as e:
        print(f"Error verifying user: {e}")
        return {"success": False, "message": f"Database error: {str(e)}"}


def create_user(username: str, email: str, password: str, full_name: str = None) -> dict:
    """Create a new user"""
    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}
        
        cursor = conn.cursor()
        password_hash = hash_password(password)
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name)
                VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, full_name
            ''', (username, email, password_hash, full_name))
            
            user = cursor.fetchone()
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "user": {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "full_name": user[3]
                }
            }
        except psycopg2.IntegrityError as e:
            conn.rollback()
            cursor.close()
            conn.close()
            
            if "username" in str(e):
                return {"success": False, "message": "Username already exists"}
            elif "email" in str(e):
                return {"success": False, "message": "Email already registered"}
            else:
                return {"success": False, "message": "User creation failed"}
                
    except Exception as e:
        print(f"Error creating user: {e}")
        return {"success": False, "message": f"Database error: {str(e)}"}


def login_user(user_data: dict):
    """Store user data in Streamlit session state"""
    st.session_state['authenticated'] = True
    st.session_state['user_id'] = user_data['id']
    st.session_state['username'] = user_data['username']
    st.session_state['email'] = user_data['email']
    st.session_state['full_name'] = user_data.get('full_name', '')


def logout_user():
    """Clear user data from Streamlit session state"""
    if 'authenticated' in st.session_state:
        del st.session_state['authenticated']
    if 'user_id' in st.session_state:
        del st.session_state['user_id']
    if 'username' in st.session_state:
        del st.session_state['username']
    if 'email' in st.session_state:
        del st.session_state['email']
    if 'full_name' in st.session_state:
        del st.session_state['full_name']


def require_auth():
    """Check if user is authenticated, redirect to login if not"""
    if 'authenticated' not in st.session_state or not st.session_state.get('authenticated'):
        return False
    return True


def get_current_user_id() -> str:
    """Get current logged-in user ID"""
    if require_auth():
        return str(st.session_state.get('user_id'))
    return None


def redirect_to_login():
    """Send user to login page."""
    try:
        st.switch_page("pages/0_Login.py")
    except Exception:
        st.error("Please login first from the Login page in the sidebar.")
        st.stop()


def redirect_to_home():
    """Send user to main dashboard."""
    try:
        st.switch_page("app.py")
    except Exception:
        st.info("You are already logged in. Use the sidebar to navigate.")


def hide_default_sidebar_nav():
    """Hide Streamlit's built-in multi-page navigation sidebar."""
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_authenticated_sidebar(active_page: str):
    """Render custom navigation links for authenticated users."""
    if not require_auth():
        return

    st.markdown("### Navigation")
    st.page_link("app.py", label="Dashboard", disabled=active_page == "dashboard")
    st.page_link(
        "pages/1_YouTube_Channels_Table.py",
        label="YouTube Channels",
        disabled=active_page == "youtube_channels",
    )
   
    st.markdown("---")


def _get_mailer():
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return None
    try:
        return yagmail.SMTP(EMAIL_SENDER, EMAIL_PASSWORD)
    except Exception as exc:
        print(f"Unable to initialize email client: {exc}")
        return None


def request_password_reset(identifier: str) -> dict:
    """Generate OTP and email it to the user"""
    if not identifier:
        return {"success": False, "message": "Please enter username or email"}

    mailer = _get_mailer()
    if not mailer:
        return {"success": False, "message": "Email service not configured. Please contact administrator."}

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT id, username, email
            FROM users
            WHERE username = %s OR email = %s
            ''',
            (identifier, identifier)
        )
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return {"success": False, "message": "User not found"}

        user_id, username, email = user

        otp = f"{random.randint(100000, 999999)}"
        expires_at = datetime.utcnow() + timedelta(minutes=RESET_OTP_EXPIRY_MINUTES)

        cursor.execute(
            '''
            UPDATE password_reset_tokens
            SET used = TRUE
            WHERE user_id = %s AND used = FALSE
            ''',
            (user_id,)
        )

        cursor.execute(
            '''
            INSERT INTO password_reset_tokens (user_id, otp, expires_at)
            VALUES (%s, %s, %s)
            ''',
            (user_id, otp, expires_at)
        )

        conn.commit()
        cursor.close()
        conn.close()

        try:
            mailer.send(
                to=email,
                subject="LinkedIn Toolkit Password Reset OTP",
                contents=(
                    f"Hello {username},\n\n"
                    f"Your one-time password (OTP) to reset your LinkedIn Toolkit account is: {otp}\n\n"
                    f"This code is valid for {RESET_OTP_EXPIRY_MINUTES} minutes.\n"
                    f"If you did not request this, please ignore this email.\n\n"
                    f"- LinkedIn Toolkit"
                )
            )
        except Exception as exc:
            print(f"Failed to send OTP email: {exc}")
            return {
                "success": False,
                "message": "Failed to send OTP email. Please verify email credentials."
            }

        return {
            "success": True,
            "message": f"OTP sent to {email}. Please check your inbox (and spam folder)."
        }

    except Exception as e:
        print(f"Error requesting password reset: {e}")
        return {"success": False, "message": f"Error generating OTP: {str(e)}"}


def reset_password_with_otp(identifier: str, otp: str, new_password: str) -> dict:
    """Verify OTP and update password"""
    if not (identifier and otp and new_password):
        return {"success": False, "message": "All fields are required"}

    if len(new_password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters long"}

    try:
        conn = get_connection()
        if not conn:
            return {"success": False, "message": "Database connection failed"}

        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT pr.id, pr.expires_at, pr.used, u.id
            FROM password_reset_tokens pr
            JOIN users u ON pr.user_id = u.id
            WHERE (u.username = %s OR u.email = %s)
                AND pr.otp = %s
            ORDER BY pr.created_at DESC
            LIMIT 1
            ''',
            (identifier, identifier, otp)
        )

        record = cursor.fetchone()
        if not record:
            cursor.close()
            conn.close()
            return {"success": False, "message": "Invalid OTP or user"}

        reset_id, expires_at, used, user_id = record

        if used:
            cursor.close()
            conn.close()
            return {"success": False, "message": "OTP has already been used"}

        if expires_at < datetime.utcnow():
            cursor.close()
            conn.close()
            return {"success": False, "message": "OTP has expired. Please request a new one"}

        password_hash = hash_password(new_password)

        cursor.execute(
            '''
            UPDATE users
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            ''',
            (password_hash, user_id)
        )

        cursor.execute(
            '''
            UPDATE password_reset_tokens
            SET used = TRUE
            WHERE id = %s
            ''',
            (reset_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return {"success": True, "message": "Password reset successfully. You can now log in with the new password."}

    except Exception as e:
        print(f"Error resetting password: {e}")
        return {"success": False, "message": f"Failed to reset password: {str(e)}"}