import speech_recognition as sr
from gtts import gTTS
import base64
from io import BytesIO

def recognize_speech():
    """Capture voice input and convert to text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except Exception as e:
        print(f"Error: {e}")
        return None

def text_to_speech(text, lang='en', return_bytes=False):
    """Convert text to speech and return bytes or play directly"""
    tts = gTTS(text=text, lang=lang)
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    
    if return_bytes:
        return fp.read()
    
    # For direct playback (if needed)
    audio_data = fp.read()
    audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{base64.b64encode(audio_data).decode('utf-8')}" type="audio/mp3">
        </audio>
    """
    return audio_html