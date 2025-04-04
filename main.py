import streamlit as st
import requests
import os
from audio_utils import recognize_speech, text_to_speech
from prompts import INITIAL_PROMPT
from dotenv import load_dotenv
import base64
import json

def get_groq_response(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-70b-8192",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 350,
        "stream": False
    }
    
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Page configuration
st.set_page_config(
    page_title="🏥 MediAI - Sequential Medical Advice",
    page_icon="🏥",
    layout="centered"
)

# Load environment variables
load_dotenv()
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Enhanced system prompt
SEQUENTIAL_PROMPT = """You are MediAI, an AI medical assistant. Follow these rules strictly:
1. FIRST provide a direct 2-3 sentence answer to the user's immediate concern
2. Include the most likely condition and immediate recommendations
3. THEN ask ONLY ONE follow-up question if absolutely necessary
4. Format responses EXACTLY as: "ANSWER: [advice] FOLLOW-UP: [question]"
5. Never combine answer and question in one audio
6. Pause 2 seconds between answer and question if both are needed"""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": INITIAL_PROMPT,
        "audio": None,
        "type": "text"
    }]
if "current_step" not in st.session_state:
    st.session_state.current_step = "awaiting_input"

# UI Components
st.title("🏥🩺 MediAI Sequential Diagnosis")
st.caption("Describe your symptoms for step-by-step medical advice")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("audio"):
            audio_base64 = base64.b64encode(message["audio"]).decode('utf-8')
            autoplay = "autoplay" if message.get("autoplay") else ""
            st.markdown(
                f'<audio controls {autoplay} style="width:100%; margin-top:10px;">'
                f'<source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">'
                f'</audio>',
                unsafe_allow_html=True
            )

# Input methods
if st.session_state.current_step == "awaiting_input":
    input_col1, input_col2 = st.columns([4, 1])
    with input_col1:
        if prompt := st.chat_input("Describe your symptoms..."):
            st.session_state.messages.append({
                "role": "user", 
                "content": prompt,
                "type": "text"
            })
            st.session_state.current_step = "processing"
            st.rerun()
    with input_col2:
        if st.button("🎤 Voice Input", use_container_width=True):
            with st.spinner("Listening..."):
                user_input = recognize_speech()
                if user_input:
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": user_input,
                        "type": "voice"
                    })
                    st.session_state.current_step = "processing"
                    st.rerun()

# Generate and handle responses
if st.session_state.current_step == "processing":
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        chat_history = [{"role": "system", "content": SEQUENTIAL_PROMPT}]
        chat_history.extend([
            {"role": m["role"], "content": m["content"]} 
            for m in st.session_state.messages[-3:]
        ])
        
        full_response = get_groq_response(chat_history)
        
        if full_response:
            if "ANSWER:" in full_response:
                parts = full_response.split("FOLLOW-UP:")
                answer = parts[0].replace("ANSWER:", "").strip()
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "audio": text_to_speech(answer, return_bytes=True),
                    "autoplay": True,
                    "type": "answer"
                })
                
                if len(parts) > 1 and parts[1].strip():
                    follow_up = parts[1].strip()
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": follow_up,
                        "audio": text_to_speech(follow_up, return_bytes=True),
                        "autoplay": False,
                        "type": "question"
                    })
                
                st.session_state.current_step = "awaiting_input"
                st.rerun()

# Emergency notice
st.warning("""
🚨 For emergencies, call your local emergency number immediately. 
This AI cannot handle life-threatening conditions.
""")

# Footer
st.markdown("""
---
<small>MediAI Sequential Diagnosis v1.0 | Not a substitute for professional medical care</small>
""", unsafe_allow_html=True)
