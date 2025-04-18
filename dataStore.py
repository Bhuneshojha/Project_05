import streamlit as st
import hashlib
import json
import os
import time
from cryptography.fernet import Fernet 
from base64 import urlsafe_b64decode
from hashlib import pbkdf2_hmac


# Data store 
DATA_FILE = "secure_data.json"
SALT = b"secure_salt_value"
LOCKOUT_DURATION = 60


# Login Section 
if "aunthenticated_user" not in st.session_state:
    st.session_state.authenticated_user = None
if "failed_attempts"  not in st.session_state:
    st.session_state.failed_attempts = 0
if "lockout_time" not in st.session_state:
    st.session_state.lockout_time = 0

 # Data is load
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)     
    return{}
def save_data(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)          
def generate_key(passkey):
    key = pbkdf2_hmac('sha256',passkey.encode(),SALT,100000)
    return urlsafe_b64decode(key)
def hash_password(password):
    return hashlib.pbkdf2_hmac('sha256',password.encode(),SALT,100000).hex()

 #cryptography.fernet 

def encrypt_text(text,key):
    chiper = Fernet(generate_key(key))
    return chiper.encrypt(text.encode()).decode()

def decrypt_text(encrypt_text,key):
    try:
        chiper = Fernet(generate_key(key))
        return chiper.decrypt(encrypt_text.encode()).decode()
    except:
        return None
stored_Data = load_data()

st.title("🌐Secure Data Encryption System")
menu = ["Home","Register","Login","Store Data","Retrieve Data"]
choice = st.sidebar.selectbox("Navigation",menu)

if choice == "Home":
    st.subheader("Hey, Welcome to My Data Encryption System🔐")
    st.markdown("Create a Streamlit app that lets users safely store and access their data using a secret passkey.Users save their data with a unique passkey.To view the data, they must enter the correct passkey.If someone keeps guessing wrong, the app sends them back to the login screen.Everything runs in memory—no need for any external database!")

elif choice == "Register":
    st.subheader("✍️Register new user")
    userName = st.text_input("choose Username")
    password = st.text_input("Choose Password",type="password")

    if st.button("Register"):
        if userName in stored_Data:
            st.warning(" ❗user exisits already")
        else:
            stored_Data[userName] = {
                "password": hash_password(password),
                "data": []

            }    
            save_data(stored_Data)
            st.success("✔️User register successfully")
    else:
        st.error("Both fields are required.")
elif choice == "Login":
    st.subheader("☁️User Login")   


    if time.time() < st.session_state.lockout_time:
        remaining = int(st.session_state.lockout_time - time.time())
        st.error(f"too many failed attempts. please wait {remaining} seconds only⏳") 
        st.stop()
    userName = st.text_input("Username")
    password = st.text_input("Password",type="password")

    if st.button("Login"):
        if userName in stored_Data and stored_Data[userName]["password"] == hash_password(password):
            st.session_state.aunthicated_user = userName
            st.session_state.failed_attempts = 0
            st.success(f"welcome {userName}🙋‍♂️")    
        else:
             st.session_state.failed_attempts +=1
             remaining = 3 - st.session_state.failed_attempts
             st.error(f"❌ Invalid Credentials! Attempts left: {remaining}")

             if st.session_state.failed_attemps >= 3:
                 st.session_state.lockot_time = time.time() + LOCKOUT_DURATION
                 st.error("Too many failed attempts. Locked for 60 seconds") 
                 st.stop()
# Data Store Section
elif choice == "Store Data":
    if not st.session_state.aunthicated_user:
        st.warning("👉 Please login first to store data.")
    else:
        st.subheader("🔐Store your Encypted Data")
        data = st.text_area("Enter your data to encrypt") 
        passkey = st.text_input("Encryption key",type="password")

        if st.button("Encrypt and Store"):
            if data and passkey:
                encrypted_data = encrypt_text(data,passkey)
                stored_Data[st.session_state.aunthicated_user]["data"].append(encrypted_data)
                save_data(stored_Data)
                st.success("✔️Data stored successfully")
            else:
                st.error("All fields are required to fill.") 
# data retrival section
elif choice == "Retrieve Data":
    if not st.session_state.aunthicated_user:
        st.warning("👉 Please login first to retrieve data.")
    else:
        st.subheader("🔎Retrieve your Encrypted Data")
        user_data = stored_Data.get(st.session_state.aunthicated_user, {}).get("data", [])


        if not user_data:
            st.warning("No data found for this user.")
        else:
            st.write("Your Encrypted Data:")
            for i, data in enumerate(user_data):
                st.code(data, language="text")

            encrypted_input= st.text_area("Enter the encrypted data to decrypt")
            passkey = st.text_input("Enter passkey to decrypt",type="password")     

            if st.button("Decrypt"):
                result = decrypt_text(encrypted_input,passkey)

                if result:
                    st.success(f"✔️Decrypted Data: {result}")   
                else:
                    st.error("❌ Decryption failed. Please check your passkey or data.")     
