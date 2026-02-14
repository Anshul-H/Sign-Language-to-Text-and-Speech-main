import pickle
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import tkinter as tk
from tkinter import StringVar, Label, Button, Frame
from PIL import Image, ImageTk
import threading
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.5, max_num_hands=1)

# TTS setup with error handling
print("Initializing audio system...")
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)
    print("✓ Audio system ready")
except Exception as e:
    print(f"✗ Audio initialization failed: {e}")
    engine = None

labels_dict = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M',
    13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y',
    25: 'Z', 26: '0', 27: '1', 28: '2', 29: '3', 30: '4', 31: '5', 32: '6', 33: '7', 34: '8', 35: '9',
    36: ' ', 37: '.'
}

stabilization_buffer = []
word_buffer = ""
sentence = ""
last_registered_time = time.time()
is_speaking = False

def speak_text(text):
    global is_speaking
    if not text or text == "N/A" or not engine or is_speaking:
        return
    
    def tts_thread():
        global is_speaking
        try:
            is_speaking = True
            print(f"🔊 Speaking: {text}")
            engine.say(text)
            engine.runAndWait()
            is_speaking = False
        except Exception as e:
            print(f"Speech error: {e}")
            is_speaking = False
    
    thread = threading.Thread(target=tts_thread, daemon=True)
    thread.start()

root = tk.Tk()
root.title("Sign Language to Speech - Audio Fixed")
root.geometry("1300x650")
root.configure(bg="#2c2f33")
root.resizable(False, False)

current_alphabet = StringVar(value="Ready")
current_word = StringVar(value="")
current_sentence = StringVar(value="")
is_paused = StringVar(value="False")
audio_status = StringVar(value="🔊 Audio: Ready" if engine else "🔇 Audio: Disabled")

title_label = Label(root, text="Sign Language to Speech Conversion", font=("Arial", 28, "bold"), 
                    fg="#ffffff", bg="#2c2f33")
title_label.grid(row=0, column=0, columnspan=2, pady=10)

video_frame = Frame(root, bg="#2c2f33", bd=5, relief="solid", width=500, height=400)
video_frame.grid(row=1, column=0, rowspan=3, padx=20, pady=20)
video_frame.grid_propagate(False)

content_frame = Frame(root, bg="#2c2f33")
content_frame.grid(row=1, column=1, sticky="n", padx=(20, 40), pady=(60, 20))

button_frame = Frame(root, bg="#2c2f33")
button_frame.grid(row=3, column=1, pady=(10, 20), padx=(10, 20), sticky="n")

video_label = tk.Label(video_frame)
video_label.pack(expand=True)

Label(content_frame, text="Current Gesture:", font=("Arial", 20), fg="#ffffff", bg="#2c2f33").pack(anchor="w", pady=(0, 10))
Label(content_frame, textvariable=current_alphabet, font=("Arial", 24, "bold"), fg="#1abc9c", bg="#2c2f33").pack(anchor="center")

Label(content_frame, text="Current Word:", font=("Arial", 20), fg="#ffffff", bg="#2c2f33").pack(anchor="w", pady=(20, 10))
Label(content_frame, textvariable=current_word, font=("Arial", 20), fg="#f39c12", bg="#2c2f33", wraplength=500).pack(anchor="center")

Label(content_frame, text="Sentence:", font=("Arial", 20), fg="#ffffff", bg="#2c2f33").pack(anchor="w", pady=(20, 10))
Label(content_frame, textvariable=current_sentence, font=("Arial", 20), fg="#9b59b6", bg="#2c2f33", wraplength=500).pack(anchor="center")

Label(content_frame, textvariable=audio_status, font=("Arial", 12), fg="#00ff88", bg="#2c2f33").pack(pady=(20, 0))

def reset_sentence():
    global word_buffer, sentence
    word_buffer = ""
    sentence = ""
    current_word.set("")
    current_sentence.set("")
    current_alphabet.set("Ready")

def toggle_pause():
    if is_paused.get() == "False":
        is_paused.set("True")
        pause_button.config(text="▶️ Resume")
    else:
        is_paused.set("False")
        pause_button.config(text="⏸️ Pause")

def test_audio():
    speak_text("Audio test successful")

Button(button_frame, text="🔄 Reset", font=("Arial", 16), command=reset_sentence, 
       bg="#e74c3c", fg="#ffffff", relief="flat", height=2, width=12).grid(row=0, column=0, padx=10)

pause_button = Button(button_frame, text="⏸️ Pause", font=("Arial", 16), command=toggle_pause, 
                      bg="#3498db", fg="#ffffff", relief="flat", height=2, width=12)
pause_button.grid(row=0, column=1, padx=10)

Button(button_frame, text="🔊 Speak", font=("Arial", 16), 
       command=lambda: speak_text(current_sentence.get() if current_sentence.get() else "No text"), 
       bg="#27ae60", fg="#ffffff", relief="flat", height=2, width=12).grid(row=0, column=2, padx=10)

Button(button_frame, text="🔊 Test Audio", font=("Arial", 14), command=test_audio, 
       bg="#9b59b6", fg="#ffffff", relief="flat", height=1, width=12).grid(row=1, column=1, padx=10, pady=5)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def process_frame():
    global stabilization_buffer, word_buffer, sentence, last_registered_time

    ret, frame = cap.read()
    if not ret:
        root.after(10, process_frame)
        return

    if is_paused.get() == "True":
        cv2.putText(frame, "PAUSED", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
    else:
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                x_coords = [lm.x for lm in hand_landmarks.landmark]
                y_coords = [lm.y for lm in hand_landmarks.landmark]
                min_x, min_y = min(x_coords), min(y_coords)
                
                data_aux = []
                for lm in hand_landmarks.landmark:
                    data_aux.extend([lm.x - min_x, lm.y - min_y])

                if len(data_aux) == 42:
                    prediction = model.predict([np.asarray(data_aux)])
                    predicted_character = labels_dict[int(prediction[0])]

                    stabilization_buffer.append(predicted_character)
                    if len(stabilization_buffer) > 30:
                        stabilization_buffer.pop(0)

                    if stabilization_buffer.count(predicted_character) > 25:
                        current_time = time.time()
                        if current_time - last_registered_time > 1.5:
                            last_registered_time = current_time
                            current_alphabet.set(predicted_character)

                            if predicted_character == ' ':
                                if word_buffer.strip():
                                    speak_text(word_buffer)
                                    sentence += word_buffer + " "
                                    current_sentence.set(sentence.strip())
                                word_buffer = ""
                                current_word.set("")
                            elif predicted_character == '.':
                                if word_buffer.strip():
                                    speak_text(word_buffer)
                                    sentence += word_buffer + "."
                                    current_sentence.set(sentence.strip())
                                word_buffer = ""
                                current_word.set("")
                            else:
                                word_buffer += predicted_character
                                current_word.set(word_buffer)

                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing_styles.get_default_hand_landmarks_style(),
                                          mp_drawing_styles.get_default_hand_connections_style())

    cv2.putText(frame, f"Gesture: {current_alphabet.get()}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    video_label.imgtk = img
    video_label.configure(image=img)

    root.after(10, process_frame)

process_frame()
root.protocol("WM_DELETE_WINDOW", lambda: [cap.release(), root.destroy()])
root.mainloop()
