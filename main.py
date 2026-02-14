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

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.6, max_num_hands=2, model_complexity=0)

# Text-to-Speech setup
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
except:
    engine = None

# label mapping
labels_dict = {
    0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'I', 9: 'J', 10: 'K', 11: 'L', 12: 'M',
    13: 'N', 14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U', 21: 'V', 22: 'W', 23: 'X', 24: 'Y',
    25: 'Z', 26: '0', 27: '1', 28: '2', 29: '3', 30: '4', 31: '5', 32: '6', 33: '7', 34: '8', 35: '9',
    36: ' ',
    37: '.'
}
expected_features = 42

# Initialize buffers and history
stabilization_buffer = []
stable_char = None
word_buffer = ""
sentence = ""

# Speak text in a separate thread
def speak_text(text):
    if not text or text == "N/A" or not engine:
        return
    def tts_thread():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=tts_thread, daemon=True).start()


# GUI Setup
root = tk.Tk()
root.title("🤟 Sign Language AI Pro")
root.geometry("1600x900")
root.configure(bg="#0a0e27")
root.resizable(False, False)  # Disable resizing

# Variables for GUI
current_alphabet = StringVar(value="N/A")
current_word = StringVar(value="N/A")
current_sentence = StringVar(value="N/A")
is_paused = StringVar(value="False")

# Header
header = Frame(root, bg="#16213e", height=80)
header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
header.grid_propagate(False)

title_label = Label(header, text="🤟 Sign Language AI Pro", font=("Segoe UI", 36, "bold"), fg="#00d4ff", bg="#16213e")
title_label.pack(side="left", padx=30, pady=10)

subtitle = Label(header, text="Two-Hand Detection • Optimized • Real-time", font=("Segoe UI", 14), fg="#aaa", bg="#16213e")
subtitle.pack(side="left", padx=10)

# Video Panel
video_panel = Frame(root, bg="#0a0e27")
video_panel.grid(row=1, column=0, padx=15, pady=10, sticky="n")

video_frame = Frame(video_panel, bg="#000", bd=3, relief="solid", width=700, height=525)
video_frame.pack()
video_frame.pack_propagate(False)

video_label = Label(video_frame, bg="#000")
video_label.pack(expand=True, fill="both")

# Status bar
status_bar = Frame(video_panel, bg="#16213e", bd=2, relief="solid")
status_bar.pack(fill="x", pady=(10, 0))

Label(status_bar, text="📊", font=("Segoe UI", 14), fg="#fff", bg="#16213e").pack(side="left", padx=10)
status_label = Label(status_bar, text="Ready", font=("Segoe UI", 12, "bold"), fg="#00ff88", bg="#16213e")
status_label.pack(side="left", padx=5)

# Output Panel
output_panel = Frame(root, bg="#0a0e27")
output_panel.grid(row=1, column=1, padx=15, pady=10, sticky="n")

# Gesture Card
gesture_card = Frame(output_panel, bg="#16213e", bd=3, relief="solid", width=450, height=150)
gesture_card.pack(pady=10)
gesture_card.pack_propagate(False)

Label(gesture_card, text="CURRENT GESTURE", font=("Segoe UI", 12, "bold"), fg="#888", bg="#16213e").pack(pady=(15, 5))
Label(gesture_card, textvariable=current_alphabet, font=("Arial", 60, "bold"), fg="#00d4ff", bg="#16213e").pack()

# Word Card
word_card = Frame(output_panel, bg="#16213e", bd=3, relief="solid", width=450, height=110)
word_card.pack(pady=10)
word_card.pack_propagate(False)

Label(word_card, text="CURRENT WORD", font=("Segoe UI", 11, "bold"), fg="#888", bg="#16213e").pack(pady=(10, 5))
Label(word_card, textvariable=current_word, font=("Segoe UI", 28, "bold"), fg="#ffaa00", bg="#16213e", wraplength=420).pack()

# Sentence Card
sentence_card = Frame(output_panel, bg="#16213e", bd=3, relief="solid", width=450, height=250)
sentence_card.pack(pady=10)
sentence_card.pack_propagate(False)

Label(sentence_card, text="TRANSLATED SENTENCE", font=("Segoe UI", 11, "bold"), fg="#888", bg="#16213e").pack(pady=(10, 5))
from tkinter import Text, Scrollbar
sentence_text = Text(sentence_card, font=("Segoe UI", 13), fg="#fff", bg="#0f3460", wrap="word", height=10, width=45, bd=0, padx=10, pady=10)
sentence_text.pack(pady=5, padx=10, fill="both", expand=True)

# Controls
control_panel = Frame(output_panel, bg="#0a0e27")
control_panel.pack(pady=10)

def create_btn(parent, text, cmd, bg, row, col):
    btn = Button(parent, text=text, font=("Segoe UI", 11, "bold"), command=cmd, bg=bg, fg="#fff", relief="flat", height=2, width=14, cursor="hand2", bd=0)
    btn.grid(row=row, column=col, padx=6, pady=5)
    return btn

def reset_sentence():
    global word_buffer, sentence
    word_buffer = ""
    sentence = ""
    current_word.set("")
    current_sentence.set("")
    current_alphabet.set("Ready")
    sentence_text.delete(1.0, tk.END)

def toggle_pause():
    if is_paused.get() == "False":
        is_paused.set("True")
        pause_button.config(text="▶️ Resume", bg="#27ae60")
        status_label.config(text="Paused", fg="#ffaa00")
    else:
        is_paused.set("False")
        pause_button.config(text="⏸️ Pause", bg="#3498db")
        status_label.config(text="Active", fg="#00ff88")

pause_button = create_btn(control_panel, "⏸️ Pause", toggle_pause, "#3498db", 0, 0)
create_btn(control_panel, "🔊 Speak", lambda: speak_text(sentence_text.get(1.0, tk.END)), "#27ae60", 0, 1)
create_btn(control_panel, "🔄 Reset", reset_sentence, "#e74c3c", 1, 0)
create_btn(control_panel, "⬅️ Undo", lambda: None, "#f39c12", 1, 1)

# Video Capture
cap = cv2.VideoCapture(0)

# Set camera feed size
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Variables for stabilization timing
last_registered_time = time.time()
registration_delay = 1.2  # Minimum delay (in seconds) before registering the same character again

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

            # Ensure valid data
            if len(data_aux) < expected_features:
                data_aux.extend([0] * (expected_features - len(data_aux)))
            elif len(data_aux) > expected_features:
                data_aux = data_aux[:expected_features]

            # Predict gesture
            prediction = model.predict([np.asarray(data_aux)])
            predicted_character = labels_dict[int(prediction[0])]

            # Stabilization logic
            stabilization_buffer.append(predicted_character)
            if len(stabilization_buffer) > 20:
                stabilization_buffer.pop(0)

            if stabilization_buffer.count(predicted_character) > 15:
                # Register the character only if enough time has passed since the last registration
                current_time = time.time()
                if current_time - last_registered_time > registration_delay:
                    stable_char = predicted_character
                    last_registered_time = current_time  # Update last registered time
                    current_alphabet.set(stable_char)

                    # Handle word and sentence formation
                    if stable_char == ' ':
                        if word_buffer.strip():
                            speak_text(word_buffer)
                            sentence += word_buffer + " "
                            sentence_text.delete(1.0, tk.END)
                            sentence_text.insert(1.0, sentence.strip())
                        word_buffer = ""
                        current_word.set("")
                    elif stable_char == '.':
                        if word_buffer.strip():
                            speak_text(word_buffer)
                            sentence += word_buffer + "."
                            sentence_text.delete(1.0, tk.END)
                            sentence_text.insert(1.0, sentence.strip())
                        word_buffer = ""
                        current_word.set("")
                    else:
                        word_buffer += stable_char
                        current_word.set(word_buffer)

            # Draw landmarks and bounding box
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                      mp_drawing_styles.get_default_hand_landmarks_style(),
                                      mp_drawing_styles.get_default_hand_connections_style())

    # Draw alphabet on the video feed
    cv2.putText(frame, f"Alphabet: {current_alphabet.get()}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # Yellow color

    # Update video feed in GUI
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = img_tk
    video_label.configure(image=img_tk)

    root.after(10, process_frame)


# Start processing frames
process_frame()
root.mainloop()
