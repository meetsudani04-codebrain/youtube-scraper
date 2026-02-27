import streamlit as st
from config.auth import (
    verify_user,
    create_user,
    login_user,
    init_auth_tables,
    require_auth,
    request_password_reset,
    reset_password_with_otp,
    redirect_to_home,
    hide_default_sidebar_nav,
)

# Initialize auth tables on first load
if 'auth_initialized' not in st.session_state:
    init_auth_tables()
    st.session_state['auth_initialized'] = True

st.set_page_config(
    page_title="Login - LinkedIn Job Scraper",
    page_icon="",
    layout="centered"
)

# If already authenticated, go straight to home
if require_auth():
    redirect_to_home()
    st.stop()

hide_default_sidebar_nav()

st.title("Login / Register")

# Tabs for Login and Register and Forgot Password
tab1, tab2, tab3 = st.tabs(["Login", "Register", "Forgot Password"])

with tab1:
    st.subheader("Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", type="primary", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                result = verify_user(username, password)
                if result["success"]:
                    login_user(result["user"])
                    st.success(f"Welcome back, {result['user']['username']}!")
                    st.info("Redirecting to main app...")
                    st.rerun()
                else:
                    st.error(f"{result['message']}")

with tab2:
    st.subheader("Create New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a username")
        email = st.text_input("Email", placeholder="Enter your email")
        full_name = st.text_input("Full Name (Optional)", placeholder="Enter your full name")
        password = st.text_input("Password", type="password", placeholder="Choose a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        submit = st.form_submit_button("Register", type="primary", use_container_width=True)
        
        if submit:
            if not username or not email or not password:
                st.error("Please fill in all required fields (Username, Email, Password)")
            elif password != confirm_password:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                result = create_user(username, email, password, full_name)
                if result["success"]:
                    st.success(f"Account created successfully! Welcome, {result['user']['username']}!")
                    login_user(result["user"])
                    st.info("Redirecting to main app...")
                    st.rerun()
                else:
                    st.error(f"{result['message']}")

with tab3:
    st.subheader("Reset Password via Email OTP")
    st.caption("Use your username or email to request a one-time password (OTP) sent to your inbox.")

    st.markdown("**Step 1: Request OTP**")
    with st.form("request_reset_form"):
        reset_identifier = st.text_input("Username or Email", key="reset_identifier")
        submit_request = st.form_submit_button("Send OTP", use_container_width=True)

        if submit_request:
            clean_identifier = reset_identifier.strip()
            result = request_password_reset(clean_identifier)
            if result["success"]:
                st.session_state["pending_reset_identifier"] = clean_identifier
                st.success(result["message"])
            else:
                st.error(result["message"])

    st.markdown("**Step 2: Verify OTP and Set New Password**")
    with st.form("verify_reset_form"):
        otp_code = st.text_input("OTP from Email", max_chars=6)
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit_reset = st.form_submit_button("Reset Password", use_container_width=True)

        if submit_reset:
            reset_identifier = st.session_state.get("pending_reset_identifier", "").strip()
            if not reset_identifier:
                st.error("No OTP request found. Please complete Step 1 first.")
            elif not otp_code or not new_password or not confirm_password:
                st.error("All fields are required")
            elif new_password != confirm_password:
                st.error("New passwords do not match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters long")
            else:
                result = reset_password_with_otp(
                    reset_identifier,
                    otp_code.strip(),
                    new_password.strip(),
                )
                if result["success"]:
                    st.session_state.pop("pending_reset_identifier", None)
                    st.success(result["message"])
                else:
                    st.error(result["message"])