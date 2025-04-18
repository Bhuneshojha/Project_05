import streamlit as st
import hashlib
import json
import os
import time
from cryptography.fernet import Fernet 
from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac

# Constants
DATA_FILE = "secure_data.json"
SALT = b"secure_salt_value"
LOCKOUT_DURATION = 60

# Session state initialization
if "authenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0
if "lockout_time" not in st.session_state:
    st.session_state.lockout_time = 0

# Load stored data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# Generate encryption key
def generate_key(passkey):
    key = pbkdf2_hmac('sha256', passkey.encode(), SALT, 100000)
    return urlsafe_b64encode(key)  # Fernet requires a 32-byte base64-encoded key

# Hash password
def hash_password(password):
    return hashlib.pbkdf2_hmac('sha256', password.encode(), SALT, 100000).hex()

# Encrypt text
def encrypt_text(text, key):
    cipher = Fernet(generate_key(key))
    return cipher.encrypt(text.encode()).decode()

# Decrypt text
def decrypt_text(encrypted_text, key):
    try:
        cipher = Fernet(generate_key(key))
        return cipher.decrypt(encrypted_text.encode()).decode()
    except:
        return None

stored_data = load_data()

st.title("🌐 Secure Data Encryption System")
menu = ["Home", "Register", "Login", "Store Data", "Retrieve Data"]
choice = st.sidebar.selectbox("Navigation", menu)

# Home Page
if choice == "Home":
    st.subheader("Hey, Welcome to My Data Encryption System 🔐")
    st.markdown("""
    - Safely store and access your data using a secret passkey.
    - Data is encrypted with your passkey.
    - Wrong guesses will lock access temporarily.
    - Everything runs in memory—no external DB!
    """)

# Register Page
elif choice == "Register":
    st.subheader("✍️ Register New User")
    userName = st.text_input("Choose Username")
    password = st.text_input("Choose Password", type="password")

    if st.button("Register"):
        if userName and password:
            if userName in stored_data:
                st.warning("❗User already exists")
            else:
                stored_data[userName] = {
                    "password": hash_password(password),
                    "data": []
                }
                save_data(stored_data)
                st.success("✔️ User registered successfully")
        else:
            st.error("Both fields are required.")

# Login Page
elif choice == "Login":
    st.subheader("☁️ User Login")

    if time.time() < st.session_state.lockout_time:
        remaining = int(st.session_state.lockout_time - time.time())
        st.error(f"Too many failed attempts. Please wait {remaining} seconds ⏳")
        st.stop()

    userName = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if userName in stored_data and stored_data[userName]["password"] == hash_password(password):
            st.session_state.authenticated_user = userName
            st.session_state.failed_attempts = 0
            st.success(f"Welcome {userName} 🙋‍♂️")
        else:
            st.session_state.failed_attempts += 1
            remaining = 3 - st.session_state.failed_attempts
            st.error(f"❌ Invalid credentials! Attempts left: {remaining}")

            if st.session_state.failed_attempts >= 3:
                st.session_state.lockout_time = time.time() + LOCKOUT_DURATION
                st.error("Too many failed attempts. Locked for 60 seconds")
                st.stop()

# Store Data Page
elif choice == "Store Data":
    if not st.session_state.authenticated_user:
        st.warning("👉 Please login first to store data.")
    else:
        st.subheader("🔐 Store Your Encrypted Data")
        data = st.text_area("Enter your data to encrypt")
        passkey = st.text_input("Encryption key", type="password")

        if st.button("Encrypt and Store"):
            if data and passkey:
                encrypted_data = encrypt_text(data, passkey)
                stored_data[st.session_state.authenticated_user]["data"].append(encrypted_data)
                save_data(stored_data)
                st.success("✔️ Data stored successfully")
            else:
                st.error("All fields are required.")

# Retrieve Data Page
elif choice == "Retrieve Data":
    if not st.session_state.authenticated_user:
        st.warning("👉 Please login first to retrieve data.")
    else:
        st.subheader("🔎 Retrieve Your Encrypted Data")
        user_data = stored_data.get(st.session_state.authenticated_user, {}).get("data", [])

        if not user_data:
            st.warning("No data found for this user.")
        else:
            st.write("Your Encrypted Data:")
            for i, data in enumerate(user_data):
                st.code(data, language="text")

            encrypted_input = st.text_area("Enter the encrypted data to decrypt")
            passkey = st.text_input("Enter passkey to decrypt", type="password")

            if st.button("Decrypt"):
                result = decrypt_text(encrypted_input, passkey)
                if result:
                    st.success(f"✔️ Decrypted Data: {result}")
                else:
                    st.error("❌ Decryption failed. Please check your passkey or data.")
