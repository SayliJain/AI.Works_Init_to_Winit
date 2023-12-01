from flask import Flask, render_template, request
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import base64
from io import BytesIO
import whisper
from transformers import pipeline
import os
import logging
from tkinter import filedialog, Tk

logging.basicConfig(filename='demo.log', encoding='utf-8', level=logging.ERROR)

app = Flask(__name__)

def handle_upload():
    root = Tk()
    root.withdraw()  # Hide the main window

    # Ask user to select a file
    file_path = filedialog.askopenfilename()
    print(f'Selected file: {file_path}')

    return file_path

def load_whisper_model(model_name: str = "medium"):
    return whisper.load_model(model_name)

def transcribe_audio_to_text(model, audio_path: str, language: str = "English"):
    return model.transcribe(audio_path, fp16=False, language=language)

def save_text_to_file(text: str, file_name: str):
    try:
        with open(file_name, "w+") as file:
            file.write(text)
    except (IOError, OSError, FileNotFoundError, PermissionError) as e:
        logging.debug(f"Error in file operation: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    target_language = request.form['target_language']
    user_text = request.form['user_text']
    
    # Handling file upload
    if 'file_input' in request.files:
        uploaded_file = request.files['file_input']
        if uploaded_file.filename != '':
            text_from_file = uploaded_file.read().decode('utf-8')
            translated_text_from_file = translate_text(text_from_file, target_language)
            tts_output_from_file = tts(translated_text_from_file, target_language)
            return render_template('result.html', original_text=text_from_file, translated_text=translated_text_from_file, audio_file=tts_output_from_file)
    
    # Handling text input
    if user_text:
        text = user_text
    else:
        file_path = handle_upload()
        model = load_whisper_model()
        result = transcribe_audio_to_text(model, file_path)
        print(result['text'])
        save_text_to_file(result["text"], 'transcribed_text.txt')
        text = result['text']
    
    translated_text = translate_text(text, target_language)
    print(f"\nOriginal Text: {text}")
    print(f"Translated Text: {translated_text}")
    
    tts_output = tts(translated_text, target_language)
    
    return render_template('result.html', original_text=text, translated_text=translated_text, audio_file=tts_output)

def translate_text(text, target_language):
    translator = Translator()
    translation = translator.translate(text, dest=target_language)
    return translation.text

def tts(text, target_language):
    tts = gTTS(text=text, lang=target_language)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    audio_data = audio_file.read()
    encoded_audio = base64.b64encode(audio_data).decode('utf-8')
    return f"data:audio/mpeg;base64,{encoded_audio}"

if __name__ == '__main__':
    app.run(debug=True)
