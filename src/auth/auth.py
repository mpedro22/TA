import streamlit as st
import hashlib
import json
import os
from typing import Dict, Optional

# File untuk menyimpan data user
USERS_FILE = "data/users.json"

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> Dict:
    """Load users from JSON file"""
    if not os.path.exists(USERS_FILE):
        # Create default admin user
        default_users = {
            "admin": {
                "email": "admin@gmail.com",
                "username": "admin",
                "password": hash_password("admin123"),
                "is_admin": True
            }
        }
        save_users(default_users)
        return default_users
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users: Dict):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def authenticate(username: str, password: str) -> Optional[Dict]:
    """Authenticate user"""
    users = load_users()
    hashed_password = hash_password(password)
    
    # Check by username
    if username in users and users[username]["password"] == hashed_password:
        return users[username]
    
    # Check by email
    for user_data in users.values():
        if user_data["email"] == username and user_data["password"] == hashed_password:
            return user_data
    
    return None

def create_user(email: str, username: str, password: str) -> bool:
    """Create new user (only admin can do this)"""
    users = load_users()
    
    # Check if username or email already exists
    if username in users:
        return False
    
    for user_data in users.values():
        if user_data["email"] == email:
            return False
    
    # Add new user
    users[username] = {
        "email": email,
        "username": username,
        "password": hash_password(password),
        "is_admin": False
    }
    
    save_users(users)
    return True

def is_logged_in() -> bool:
    """Check if user is logged in"""
    return "user" in st.session_state and st.session_state.user is not None

def is_admin() -> bool:
    """Check if current user is admin"""
    if not is_logged_in():
        return False
    return st.session_state.user.get("is_admin", False)

def get_current_user() -> Optional[Dict]:
    """Get current logged in user"""
    if is_logged_in():
        return st.session_state.user
    return None

# auth.py

def logout():
    """Logout current user and clear all related state."""
    # Hapus semua kunci yang relevan dari session_state
    keys_to_delete = ["user", "current_page"]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    
    # Hapus semua parameter dari URL
    st.query_params.clear()
