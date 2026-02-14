import pickle
import cv2
import mediapipe as mp
import numpy as np
import pyttsx3
import tkinter as tk
from tkinter import StringVar, Label, Button, Frame, Text, Scrollbar, messagebox, filedialog, Scale, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
import threading
import time
import warnings
import json
from datetime import datetime
import os
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
session_stats = {"gestures": 0, "words": 0, "sentences": 0, "start_time": time.time(), "session_duration": 0}
dark_mode = True
tts_rate = 150
tts_voice_index = 0
auto_speak = True
show_landmarks = True

def speak_text(text, rate=None):
    if not text.strip():
        return
    def tts_thread():
        engine.setProperty('rate', rate or tts_rate)
        engine.setProperty('voice', voices[tts_voice_index].id)
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=tts_thread, daemon=True).start()

def save_session():
    session_stats["session_duration"] = int(time.time() - session_stats["start_time"])
    data = {
        "sentence": sentence_text.get(1.0, tk.END).strip(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stats": session_stats,
        "history": gesture_history[-50:]
    }
    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
        initialfile=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    if filename:
        with open(filename, 'w') as f:
            if filename.endswith('.json'):
                json.dump(data, f, indent=4)
            else:
                f.write(f"Sign Language Session\n{'='*50}\n")
                f.write(f"Timestamp: {data['timestamp']}\n")
                f.write(f"Duration: {session_stats['session_duration']}s\n")
                f.write(f"Gestures: {session_stats['gestures']}\n")
                f.write(f"Words: {session_stats['words']}\n\n")
                f.write(f"Sentence:\n{data['sentence']}\n")
        messagebox.showinfo("✅ Success", "Session saved successfully!")

def load_session():
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
    if filename:
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                sentence_text.delete(1.0, tk.END)
                sentence_text.insert(1.0, data.get("sentence", ""))
                messagebox.showinfo("✅ Success", "Session loaded successfully!")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to load session: {str(e)}")

def export_to_clipboard():
    text = sentence_text.get(1.0, tk.END).strip()
    if text:
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("✅ Copied", "Text copied to clipboard!")

def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()

def apply_theme():
    if dark_mode:
        colors = {
            "bg": "#0a0e27", "fg": "#ffffff", "accent": "#00d4ff",
            "panel": "#16213e", "button": "#1e3a5f", "success": "#00ff88"
        }
    else:
        colors = {
            "bg": "#f5f5f5", "fg": "#000000", "accent": "#0066cc",
            "panel": "#ffffff", "button": "#e0e0e0", "success": "#00aa00"
        }
    
    root.configure(bg=colors["bg"])
    theme_button.config(text="🌙 Dark Mode" if not dark_mode else "☀️ Light Mode")

def change_voice(index):
    global tts_voice_index
    tts_voice_index = index

def update_speed(val):
    global tts_rate
    tts_rate = int(float(val))
    speed_label.config(text=f"Speed: {tts_rate}")

def toggle_auto_speak():
    global auto_speak
    auto_speak = not auto_speak
    auto_speak_btn.config(text=f"Auto-Speak: {'ON' if auto_speak else 'OFF'}", 
                          bg="#27ae60" if auto_speak else "#95a5a6")

def toggle_landmarks():
    global show_landmarks
    show_landmarks = not show_landmarks
    landmarks_btn.config(text=f"Landmarks: {'ON' if show_landmarks else 'OFF'}")

# GUI Setup
root = tk.Tk()
root.title("🤟 Sign Language AI Pro - Ultimate Edition")
root.geometry("1700x950")
root.configure(bg="#0a0e27")
root.resizable(False, False)

# Variables
current_alphabet = StringVar(value="Ready")
current_word = StringVar(value="")
current_sentence = StringVar(value="")
is_paused = StringVar(value="False")
confidence_var = StringVar(value="0%")
gesture_count = StringVar(value="0")
word_count = StringVar(value="0")
fps_var = StringVar(value="0 FPS")

# Header
header_frame = Frame(root, bg="#16213e", height=80)
header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
header_frame.grid_propagate(False)

title_label = Label(header_frame, text="🤟 Sign Language AI Pro", font=("Segoe UI", 36, "bold"), 
                    fg="#00d4ff", bg="#16213e")
title_label.pack(side="left", padx=30, pady=10)

subtitle_label = Label(header_frame, text="Real-time ASL Translation with AI", 
                       font=("Segoe UI", 14), fg="#aaaaaa", bg="#16213e")
subtitle_label.pack(side="left", padx=10)

# Left Panel - Video Feed
left_panel = Frame(root, bg="#0a0e27")
left_panel.grid(row=1, column=0, padx=15, pady=10, sticky="n")

video_frame = Frame(left_panel, bg="#000000", bd=3, relief="solid", width=700, height=525)
video_frame.pack()
video_frame.pack_propagate(False)

video_label = Label(video_frame, bg="#000000")
video_label.pack(expand=True, fill="both")

# Video Controls
video_controls = Frame(left_panel, bg="#16213e", bd=2, relief="solid")
video_controls.pack(fill="x", pady=(10, 0))

Label(video_controls, text="📊", font=("Segoe UI", 14), fg="#ffffff", bg="#16213e").pack(side="left", padx=10)
Label(video_controls, textvariable=confidence_var, font=("Segoe UI", 12, "bold"), 
      fg="#00ff88", bg="#16213e").pack(side="left", padx=5)
Label(video_controls, textvariable=fps_var, font=("Segoe UI", 12), 
      fg="#ffaa00", bg="#16213e").pack(side="left", padx=20)

landmarks_btn = Button(video_controls, text="Landmarks: ON", font=("Segoe UI", 10), 
                       command=toggle_landmarks, bg="#3498db", fg="#ffffff", relief="flat", cursor="hand2")
landmarks_btn.pack(side="right", padx=10, pady=5)

# Middle Panel - Output Display
middle_panel = Frame(root, bg="#0a0e27")
middle_panel.grid(row=1, column=1, padx=15, pady=10, sticky="n")

# Gesture Display (Large)
gesture_card = Frame(middle_panel, bg="#16213e", bd=3, relief="solid", width=450, height=150)
gesture_card.pack(pady=10)
gesture_card.pack_propagate(False)

Label(gesture_card, text="CURRENT GESTURE", font=("Segoe UI", 12, "bold"), 
      fg="#888888", bg="#16213e").pack(pady=(15, 5))
gesture_label = Label(gesture_card, textvariable=current_alphabet, font=("Arial", 60, "bold"), 
                      fg="#00d4ff", bg="#16213e")
gesture_label.pack()

# Word Display
word_card = Frame(middle_panel, bg="#16213e", bd=3, relief="solid", width=450, height=110)
word_card.pack(pady=10)
word_card.pack_propagate(False)

Label(word_card, text="CURRENT WORD", font=("Segoe UI", 11, "bold"), 
      fg="#888888", bg="#16213e").pack(pady=(10, 5))
Label(word_card, textvariable=current_word, font=("Segoe UI", 28, "bold"), 
      fg="#ffaa00", bg="#16213e", wraplength=420).pack()

# Sentence Display
sentence_card = Frame(middle_panel, bg="#16213e", bd=3, relief="solid", width=450, height=250)
sentence_card.pack(pady=10)
sentence_card.pack_propagate(False)

Label(sentence_card, text="TRANSLATED SENTENCE", font=("Segoe UI", 11, "bold"), 
      fg="#888888", bg="#16213e").pack(pady=(10, 5))

sentence_text = Text(sentence_card, font=("Segoe UI", 13), fg="#ffffff", bg="#0f3460", 
                     wrap="word", height=10, width=45, bd=0, padx=10, pady=10)
sentence_text.pack(pady=5, padx=10, fill="both", expand=True)

# Control Panel
control_panel = Frame(middle_panel, bg="#0a0e27")
control_panel.pack(pady=10)

def create_modern_button(parent, text, command, bg_color, row, col, width=14):
    btn = Button(parent, text=text, font=("Segoe UI", 11, "bold"), command=command, 
                 bg=bg_color, fg="#ffffff", relief="flat", height=2, width=width, 
                 cursor="hand2", activebackground=bg_color, bd=0)
    btn.grid(row=row, column=col, padx=6, pady=5)
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
    session_stats = {"gestures": 0, "words": 0, "sentences": 0, "start_time": time.time(), "session_duration": 0}
    update_stats()
    history_text.delete(1.0, tk.END)

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

pause_button = create_modern_button(control_panel, "⏸️ Pause", toggle_pause, "#3498db", 0, 0)
create_modern_button(control_panel, "🔊 Speak", speak_sentence, "#27ae60", 0, 1)
create_modern_button(control_panel, "⬅️ Undo", undo_last, "#f39c12", 0, 2)
create_modern_button(control_panel, "🔄 Reset", reset_all, "#e74c3c", 1, 0)
create_modern_button(control_panel, "💾 Save", save_session, "#9b59b6", 1, 1)
create_modern_button(control_panel, "📂 Load", load_session, "#34495e", 1, 2)
create_modern_button(control_panel, "📋 Copy", export_to_clipboard, "#16a085", 2, 0)
auto_speak_btn = create_modern_button(control_panel, "Auto-Speak: ON", toggle_auto_speak, "#27ae60", 2, 1)
theme_button = create_modern_button(control_panel, "☀️ Light Mode", toggle_theme, "#2c3e50", 2, 2)

# Right Panel - Settings & Stats
right_panel = Frame(root, bg="#0a0e27")
right_panel.grid(row=1, column=2, padx=15, pady=10, sticky="n")

# Statistics Card
stats_card = Frame(right_panel, bg="#16213e", bd=3, relief="solid", width=380)
stats_card.pack(pady=10)
stats_card.pack_propagate(False)

Label(stats_card, text="📊 SESSION STATISTICS", font=("Segoe UI", 14, "bold"), 
      fg="#00d4ff", bg="#16213e").pack(pady=15)

stats_grid = Frame(stats_card, bg="#16213e")
stats_grid.pack(pady=10, padx=20)

def create_stat_row(parent, label, var, row):
    Label(parent, text=label, font=("Segoe UI", 11), fg="#cccccc", bg="#16213e").grid(
        row=row, column=0, sticky="w", pady=8, padx=10)
    Label(parent, textvariable=var, font=("Segoe UI", 11, "bold"), fg="#00ff88", bg="#16213e").grid(
        row=row, column=1, sticky="e", pady=8, padx=10)

create_stat_row(stats_grid, "Gestures Detected:", gesture_count, 0)
create_stat_row(stats_grid, "Words Formed:", word_count, 1)

# Voice Settings Card
voice_card = Frame(right_panel, bg="#16213e", bd=3, relief="solid", width=380)
voice_card.pack(pady=10)
voice_card.pack_propagate(False)

Label(voice_card, text="🎙️ VOICE SETTINGS", font=("Segoe UI", 14, "bold"), 
      fg="#00d4ff", bg="#16213e").pack(pady=15)

voice_frame = Frame(voice_card, bg="#16213e")
voice_frame.pack(pady=10, padx=20, fill="x")

Label(voice_frame, text="Voice:", font=("Segoe UI", 10), fg="#cccccc", bg="#16213e").pack(anchor="w")
voice_combo = ttk.Combobox(voice_frame, values=[v.name for v in voices], state="readonly", width=30)
voice_combo.current(0)
voice_combo.bind("<<ComboboxSelected>>", lambda e: change_voice(voice_combo.current()))
voice_combo.pack(pady=5, fill="x")

Label(voice_frame, text="Speech Speed:", font=("Segoe UI", 10), fg="#cccccc", bg="#16213e").pack(anchor="w", pady=(10, 0))
speed_label = Label(voice_frame, text=f"Speed: {tts_rate}", font=("Segoe UI", 9), fg="#ffaa00", bg="#16213e")
speed_label.pack(anchor="w")

speed_scale = Scale(voice_frame, from_=50, to=300, orient="horizontal", command=update_speed,
                    bg="#16213e", fg="#ffffff", highlightthickness=0, troughcolor="#0f3460")
speed_scale.set(tts_rate)
speed_scale.pack(fill="x", pady=5)

# History Card
history_card = Frame(right_panel, bg="#16213e", bd=3, relief="solid", width=380, height=320)
history_card.pack(pady=10)
history_card.pack_propagate(False)

Label(history_card, text="📜 GESTURE HISTORY", font=("Segoe UI", 14, "bold"), 
      fg="#00d4ff", bg="#16213e").pack(pady=15)

history_scroll = Scrollbar(history_card)
history_scroll.pack(side="right", fill="y", padx=(0, 10))

history_text = Text(history_card, font=("Consolas", 9), fg="#ffffff", bg="#0f3460", 
                    wrap="word", yscrollcommand=history_scroll.set, height=15, width=40, bd=0)
history_text.pack(pady=5, padx=10, fill="both", expand=True)
history_scroll.config(command=history_text.yview)

def update_stats():
    gesture_count.set(str(session_stats["gestures"]))
    word_count.set(str(session_stats["words"]))

def add_to_history(char, confidence):
    timestamp = datetime.now().strftime("%H:%M:%S")
    gesture_history.append({"char": char, "time": timestamp, "confidence": confidence})
    history_text.insert(1.0, f"[{timestamp}] {char} ({confidence:.0f}%)\n")
    if len(history_text.get(1.0, tk.END).split('\n')) > 100:
        history_text.delete("50.0", tk.END)

# Keyboard Shortcuts
def on_key_press(event):
    if event.keysym == 'space' and event.state & 0x4:  # Ctrl+Space
        toggle_pause()
    elif event.keysym == 'r' and event.state & 0x4:  # Ctrl+R
        reset_all()
    elif event.keysym == 's' and event.state & 0x4:  # Ctrl+S
        save_session()

root.bind('<KeyPress>', on_key_press)

# Video Capture
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

frame_times = []

def process_frame():
    global stabilization_buffer, stable_char, word_buffer, sentence, last_registered_time, frame_times

    start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        root.after(10, process_frame)
        return

    if is_paused.get() == "True":
        cv2.putText(frame, "PAUSED", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = img_tk
        video_label.configure(image=img_tk)
        root.after(10, process_frame)
        return

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    confidence = 0
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
                    add_to_history(stable_char, confidence)
                    update_stats()

                    if stable_char == ' ':
                        if word_buffer.strip():
                            if auto_speak:
                                speak_text(word_buffer)
                            sentence += word_buffer + " "
                            sentence_text.delete(1.0, tk.END)
                            sentence_text.insert(1.0, sentence.strip())
                            session_stats["words"] += 1
                        word_buffer = ""
                        current_word.set("")
                    elif stable_char == '.':
                        if word_buffer.strip():
                            if auto_speak:
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

            if show_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                                          mp_drawing_styles.get_default_hand_landmarks_style(),
                                          mp_drawing_styles.get_default_hand_connections_style())

    # Enhanced overlay with modern design
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (640, 50), (22, 33, 62), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    cv2.putText(frame, f"Gesture: {current_alphabet.get()}", (15, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 212, 255), 2)
    cv2.putText(frame, f"{confidence:.0f}%", (550, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)

    # FPS calculation
    frame_times.append(time.time())
    if len(frame_times) > 30:
        frame_times.pop(0)
    if len(frame_times) > 1:
        fps = len(frame_times) / (frame_times[-1] - frame_times[0])
        fps_var.set(f"{fps:.1f} FPS")

    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img_tk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = img_tk
    video_label.configure(image=img_tk)

    root.after(10, process_frame)

# Start
process_frame()
root.protocol("WM_DELETE_WINDOW", lambda: [cap.release(), root.destroy()])
root.mainloop()
