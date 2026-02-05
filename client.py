import streamlit as st
import socket
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

st.set_page_config(page_title="Global Chat", layout="centered", page_icon="💬")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "connected" not in st.session_state:
    st.session_state.connected = False

# --- LISTENER ---
def listen_to_server(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data: break
            clean_msg = data.decode().strip()
            st.session_state.messages.append({"role": "other", "content": clean_msg})
            st.rerun() 
        except: break

# --- SIDEBAR ---
st.sidebar.title("Chat Settings")
username = st.sidebar.text_input("Your Name", placeholder="username")
if not st.session_state.connected:
    if st.sidebar.button("Connect"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 8888))
            s.sendall(f"{username}\n".encode())
            st.session_state.sock = s
            st.session_state.connected = True
            t = threading.Thread(target=listen_to_server, args=(s,), daemon=True)
            add_script_run_ctx(t)
            t.start()
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# --- CHAT AREA ---
st.title("Real-Time Chat")

@st.fragment(run_every=0.5)
def show_messages():
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "me" else "assistant"
            with st.chat_message(role):
                st.write(msg["content"])

if st.session_state.connected:
    show_messages()

    if prompt := st.chat_input("Type a message..."):
        try:
            st.session_state.sock.sendall(f"{prompt}\n".encode())
            st.session_state.messages.append({"role": "me", "content": f"You: {prompt}"})
            st.rerun()
        except:
            pass