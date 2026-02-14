import pickle
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import tkinter as tk
from tkinter import StringVar, Label, Button, Frame, Text, Scrollbar, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time
import warnings
import json
from datetime import datetime
warnings.filterwarnings("ignore", category=UserWarning)

# Load model
model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.5, max_num_hands=1)

# TTS setup
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Label mapping
labels_dict = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M',
    13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y',
    25: 'Z', 26: '0', 27: '1', 28: '2', 29: '3', 30: '4', 31: '5', 32: '6', 33: '7', 34: '8', 35: '9',
    36: ' ', 37: '.'
}
expected_features = 42

# Global variables
stabilization_buffer = []
stable_char = None
word_buffer = ""
sentence = ""
last_registered_time = time.time()
registration_delay = 1.5
gesture_history = []
confidence_scores = []
session_stats = {"gestures": 0, "words": 0, "sentences": 0, "start_time": time.time()}
dark_mode = True

def speak_text(text, rate=150):
    def tts_thread():
        engine.setProperty('rate', rate)
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=tts_thread, daemon=True).start()

def save_session():
    data = {
        "sentence": current_sentence.get(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": session_stats
    }
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("Text files", "*.txt")])
    if filename:
        with open(filename, 'w') as f:
            if filename.endswith('.json'):
                json.dump(data, f, indent=4)
            else:
                f.write(f"Sentence: {data['sentence']}\nTimestamp: {data['timestamp']}")
        messagebox.showinfo("Success", "Session saved successfully!")

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    bg = "#1a1a2e" if dark_mode else "#f0f0f0"
    fg = "#ffffff" if dark_mode else "#000000"
    root.configure(bg=bg)
    for widget in [title_label, content_frame, button_frame, stats_frame, history_frame]:
        widget.configure(bg=bg)
    theme_button.config(text="🌙 Dark" if not dark_mode else "☀️ Light")

# GUI Setup
root = tk.Tk()
root.title("Sign Language AI - Enhanced Edition")
root.geometry("1600x900")
root.configure(bg="#1a1a2e")
root.resizable(False, False)

# Variables
current_alphabet = StringVar(value="Ready")
current_word = StringVar(value="")
current_sentence = StringVar(value="")
is_paused = StringVar(value="False")
confidence_var = StringVar(value="0%")
gesture_count = StringVar(value="0")
word_count = StringVar(value="0")
speed_var = StringVar(value="Normal")

# Title
title_label = Label(root, text="🤟 Sign Language AI Translator", font=("Segoe UI", 32, "bold"), fg="#00d4ff", bg="#1a1a2e")
title_label.grid(row=0, column=0, columnspan=3, pady=15)

# Left Panel - Video
video_frame = Frame(root, bg="#16213e", bd=3, relief="solid", width=640, height=480)
video_frame.grid(row=1, column=0, rowspan=4, padx=20, pady=10, sticky="n")
video_frame.grid_propagate(False)

video_label = Label(video_frame, bg="#000000")
video_label.pack(expand=True, fill="both")

# Status bar under video
status_frame = Frame(root, bg="#16213e", bd=2, relief="solid")
status_frame.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

Label(status_frame, text="Confidence:", font=("Segoe UI", 11), fg="#ffffff", bg="#16213e").pack(side="left", padx=10)
Label(status_frame, textvariable=confidence_var, font=("Segoe UI", 11, "bold"), fg="#00ff88", bg="#16213e").pack(side="left")

Label(status_frame, text="Speed:", font=("Segoe UI", 11), fg="#ffffff", bg="#16213e").pack(side="left", padx=(20, 5))
Label(status_frame, textvariable=speed_var, font=("Segoe UI", 11, "bold"), fg="#ffaa00", bg="#16213e").pack(side="left")

# Middle Panel - Output
content_frame = Frame(root, bg="#1a1a2e")
content_frame.grid(row=1, column=1, padx=20, pady=10, sticky="n")

# Current Gesture Display
gesture_display = Frame(content_frame, bg="#16213e", bd=3, relief="solid", width=400, height=120)
gesture_display.pack(pady=10)
gesture_display.pack_propagate(False)

Label(gesture_display, text="Current Gesture", font=("Segoe UI", 14), fg="#aaaaaa", bg="#16213e").pack(pady=(10, 0))
Label(gesture_display, textvariable=current_alphabet, font=("Segoe UI", 48, "bold"), fg="#00d4ff", bg="#16213e").pack()

# Word Display
word_display = Frame(content_frame, bg="#16213e", bd=3, relief="solid", width=400, height=100)
word_display.pack(pady=10)
word_display.pack_propagate(False)

Label(word_display, text="Current Word", font=("Segoe UI", 12), fg="#aaaaaa", bg="#16213e").pack(pady=(5, 0))
Label(word_display, textvariable=current_word, font=("Segoe UI", 24, "bold"), fg="#ffaa00", bg="#16213e", wraplength=380).pack(pady=5)

# Sentence Display
sentence_display = Frame(content_frame, bg="#16213e", bd=3, relief="solid", width=400, height=200)
sentence_display.pack(pady=10)
sentence_display.pack_propagate(False)

Label(sentence_display, text="Sentence", font=("Segoe UI", 12), fg="#aaaaaa", bg="#16213e").pack(pady=(5, 0))

sentence_text = Text(sentence_display, font=("Segoe UI", 14), fg="#ffffff", bg="#0f3460", wrap="word", height=7, width=40, bd=0)
sentence_text.pack(pady=5, padx=10)

# Control Buttons
button_frame = Frame(root, bg="#1a1a2e")
button_frame.grid(row=2, column=1, pady=10)

def create_button(parent, text, command, bg_color, row, col):
    btn = Button(parent, text=text, font=("Segoe UI", 12, "bold"), command=command, bg=bg_color, fg="#ffffff", 
                 relief="flat", height=2, width=15, cursor="hand2", activebackground=bg_color, bd=0)
    btn.grid(row=row, column=col, padx=8, pady=5)
    return btn

def reset_all():
    global word_buffer, sentence, gesture_history, session_stats
    word_buffer = ""
    sentence = ""
    gesture_history = []
    current_word.set("")
    current_sentence.set("")
    current_alphabet.set("Ready")
    sentence_text.delete(1.0, tk.END)
    session_stats = {"gestures": 0, "words": 0, "sentences": 0, "start_time": time.time()}
    update_stats()

def toggle_pause():
    if is_paused.get() == "False":
        is_paused.set("True")
        pause_button.config(text="▶️ Resume", bg="#27ae60")
    else:
        is_paused.set("False")
        pause_button.config(text="⏸️ Pause", bg="#3498db")

def speak_sentence():
    text = sentence_text.get(1.0, tk.END).strip()
    if text:
        speak_text(text)

def undo_last():
    global word_buffer
    if word_buffer:
        word_buffer = word_buffer[:-1]
        current_word.set(word_buffer if word_buffer else "")

create_button(button_frame, "⏸️ Pause", toggle_pause, "#3498db", 0, 0)
pause_button = button_frame.winfo_children()[-1]

create_button(button_frame, "🔊 Speak", speak_sentence, "#27ae60", 0, 1)
create_button(button_frame, "🔄 Reset", reset_all, "#e74c3c", 1, 0)
create_button(button_frame, "⬅️ Undo", undo_last, "#f39c12", 1, 1)
create_button(button_frame, "💾 Save", save_session, "#9b59b6", 2, 0)
theme_button = create_button(button_frame, "☀️ Light", toggle_theme, "#34495e", 2, 1)

# Right Panel - Stats & History
stats_frame = Frame(root, bg="#16213e", bd=3, relief="solid", width=350)
stats_frame.grid(row=1, column=2, padx=20, pady=10, sticky="n")
stats_frame.grid_propagate(False)

Label(stats_frame, text="📊 Session Statistics", font=("Segoe UI", 16, "bold"), fg="#00d4ff", bg="#16213e").pack(pady=10)

stats_content = Frame(stats_frame, bg="#16213e")
stats_content.pack(pady=10)

Label(stats_content, text="Gestures Detected:", font=("Segoe UI", 11), fg="#ffffff", bg="#16213e").grid(row=0, column=0, sticky="w", padx=20, pady=5)
Label(stats_content, textvariable=gesture_count, font=("Segoe UI", 11, "bold"), fg="#00ff88", bg="#16213e").grid(row=0, column=1, sticky="e", padx=20)

Label(stats_content, text="Words Formed:", font=("Segoe UI", 11), fg="#ffffff", bg="#16213e").grid(row=1, column=0, sticky="w", padx=20, pady=5)
Label(stats_content, textvariable=word_count, font=("Segoe UI", 11, "bold"), fg="#00ff88", bg="#16213e").grid(row=1, column=1, sticky="e", padx=20)

# History Panel
history_frame = Frame(root, bg="#16213e", bd=3, relief="solid", width=350, height=400)
history_frame.grid(row=2, column=2, rowspan=3, padx=20, pady=10, sticky="n")
history_frame.grid_propagate(False)

Label(history_frame, text="📜 Gesture History", font=("Segoe UI", 14, "bold"), fg="#00d4ff", bg="#16213e").pack(pady=10)

history_scroll = Scrollbar(history_frame)
history_scroll.pack(side="right", fill="y")

history_text = Text(history_frame, font=("Consolas", 10), fg="#ffffff", bg="#0f3460", wrap="word", 
                    yscrollcommand=history_scroll.set, height=20, width=35, bd=0)
history_text.pack(pady=5, padx=10)
history_scroll.config(command=history_text.yview)

def update_stats():
    gesture_count.set(str(session_stats["gestures"]))
    word_count.set(str(session_stats["words"]))

def add_to_history(char):
    timestamp = datetime.now().strftime("%H:%M:%S")
    history_text.insert(1.0, f"[{timestamp}] {char}\n")
    if len(history_text.get(1.0, tk.END).split('\n')) > 100:
        history_text.delete("50.0", tk.END)

# Video Capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def process_frame():
    global stabilization_buffer, stable_char, word_buffer, sentence, last_registered_time

    ret, frame = cap.read()
    if not ret:
        return

    if is_paused.get() == "True":
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = img_tk
        video_label.configure(image=img_tk)
        root.after(10, process_frame)
        return

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            data_aux = []
            x_ = []
            y_ = []

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                x_.append(x)
                y_.append(y)

            for i in range(len(hand_landmarks.landmark)):
                x = hand_landmarks.landmark[i].x
                y = hand_landmarks.landmark[i].y
                data_aux.append(x - min(x_))
                data_aux.append(y - min(y_))

            if len(data_aux) < expected_features:
                data_aux.extend([0] * (expected_features - len(data_aux)))
            elif len(data_aux) > expected_features:
                data_aux = data_aux[:expected_features]

            prediction = model.predict([np.asarray(data_aux)])
            proba = model.predict_proba([np.asarray(data_aux)])
            confidence = np.max(proba) * 100
            confidence_var.set(f"{confidence:.1f}%")
            
            predicted_character = labels_dict[int(prediction[0])]

            stabilization_buffer.append(predicted_character)
            if len(stabilization_buffer) > 30:
                stabilization_buffer.pop(0)

            if stabilization_buffer.count(predicted_character) > 25:
                current_time = time.time()
                if current_time - last_registered_time > registration_delay:
                    stable_char = predicted_character
                    last_registered_time = current_time
                    current_alphabet.set(stable_char)
                    session_stats["gestures"] += 1
                    add_to_history(stable_char)
                    update_stats()

                    if stable_char == ' ':
                        if word_buffer.strip():
                            speak_text(word_buffer)
                            sentence += word_buffer + " "
                            sentence_text.delete(1.0, tk.END)
                            sentence_text.insert(1.0, sentence.strip())
                            session_stats["words"] += 1
                        word_buffer = ""
                        current_word.set("")
                    elif stable_char == '.':
                        if word_buffer.strip():
                            speak_text(word_buffer)
                            sentence += word_buffer + "."
                            sentence_text.delete(1.0, tk.END)
                            sentence_text.insert(1.0, sentence.strip())
                            session_stats["words"] += 1
                            session_stats["sentences"] += 1
                        word_buffer = ""
                        current_word.set("")
                    else:
                        word_buffer += stable_char
                        current_word.set(word_buffer)

            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                      mp_drawing_styles.get_default_hand_landmarks_style(),
                                      mp_drawing_styles.get_default_hand_connections_style())

    # Enhanced overlay
    cv2.putText(frame, f"Gesture: {current_alphabet.get()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(frame, f"Confidence: {confidence_var.get()}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = img_tk
    video_label.configure(image=img_tk)

    root.after(10, process_frame)

process_frame()
root.mainloop()
cap.release()
