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

model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(static_image_mode=False, min_detection_confidence=0.6, 
                       max_num_hands=2, model_complexity=0)  # Optimized: 2 hands, low complexity

try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 180)
    engine.setProperty('volume', 1.0)
except:
    engine = None

def speak(text):
    if not text or not engine:
        return
    def tts():
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass
    threading.Thread(target=tts, daemon=True).start()

labels_dict = {i: chr(65+i) if i < 26 else str(i-26) if i < 36 else [' ', '.'][i-36] 
               for i in range(38)}

buffer = []
word = ""
sentence = ""
last_time = time.time()

root = tk.Tk()
root.title("ASL AI - Optimized Two-Hand")
root.geometry("1400x700")
root.configure(bg="#1a1a2e")

alphabet_var = StringVar(value="Ready")
word_var = StringVar(value="")
sentence_var = StringVar(value="")
paused = StringVar(value="False")

Label(root, text="🤟 ASL AI - Two Hand Detection", font=("Arial", 32, "bold"), 
      fg="#00d4ff", bg="#1a1a2e").pack(pady=10)

video_frame = Frame(root, bg="#000", width=640, height=480)
video_frame.pack(side="left", padx=20, pady=20)
video_frame.pack_propagate(False)
video_label = Label(video_frame, bg="#000")
video_label.pack(expand=True, fill="both")

info_frame = Frame(root, bg="#1a1a2e")
info_frame.pack(side="right", padx=20, fill="both", expand=True)

Label(info_frame, text="Gesture", font=("Arial", 14), fg="#aaa", bg="#1a1a2e").pack()
Label(info_frame, textvariable=alphabet_var, font=("Arial", 48, "bold"), 
      fg="#00d4ff", bg="#1a1a2e").pack(pady=10)

Label(info_frame, text="Word", font=("Arial", 14), fg="#aaa", bg="#1a1a2e").pack()
Label(info_frame, textvariable=word_var, font=("Arial", 24), 
      fg="#ffaa00", bg="#1a1a2e").pack(pady=10)

Label(info_frame, text="Sentence", font=("Arial", 14), fg="#aaa", bg="#1a1a2e").pack()
Label(info_frame, textvariable=sentence_var, font=("Arial", 18), 
      fg="#fff", bg="#1a1a2e", wraplength=400).pack(pady=10)

btn_frame = Frame(info_frame, bg="#1a1a2e")
btn_frame.pack(pady=20)

Button(btn_frame, text="⏸️ Pause", command=lambda: paused.set("True" if paused.get()=="False" else "False"),
       bg="#3498db", fg="#fff", font=("Arial", 12), width=10).grid(row=0, column=0, padx=5)
Button(btn_frame, text="🔊 Speak", command=lambda: speak(sentence_var.get()),
       bg="#27ae60", fg="#fff", font=("Arial", 12), width=10).grid(row=0, column=1, padx=5)
Button(btn_frame, text="🔄 Reset", command=lambda: [globals().update({'word': '', 'sentence': ''}), 
       word_var.set(''), sentence_var.set(''), alphabet_var.set('Ready')],
       bg="#e74c3c", fg="#fff", font=("Arial", 12), width=10).grid(row=1, column=0, padx=5, pady=5)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Optimization

def process():
    global buffer, word, sentence, last_time
    
    ret, frame = cap.read()
    if not ret:
        root.after(10, process)
        return
    
    if paused.get() == "True":
        cv2.putText(frame, "PAUSED", (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 3)
    else:
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if results.multi_hand_landmarks:
            for idx, hand_lm in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)
                
                if idx == 0:  # Process only first hand for gesture
                    x_coords = [lm.x for lm in hand_lm.landmark]
                    y_coords = [lm.y for lm in hand_lm.landmark]
                    min_x, min_y = min(x_coords), min(y_coords)
                    
                    features = []
                    for lm in hand_lm.landmark:
                        features.extend([lm.x - min_x, lm.y - min_y])
                    
                    if len(features) == 42:
                        pred = model.predict([features])[0]
                        char = labels_dict[int(pred)]
                        
                        buffer.append(char)
                        if len(buffer) > 20:
                            buffer.pop(0)
                        
                        if buffer.count(char) > 15 and time.time() - last_time > 1.2:
                            last_time = time.time()
                            alphabet_var.set(char)
                            
                            if char == ' ':
                                if word:
                                    speak(word)
                                    sentence += word + " "
                                    sentence_var.set(sentence.strip())
                                    word = ""
                                    word_var.set("")
                            elif char == '.':
                                if word:
                                    speak(word)
                                    sentence += word + "."
                                    sentence_var.set(sentence.strip())
                                    word = ""
                                    word_var.set("")
                            else:
                                word += char
                                word_var.set(word)
    
    cv2.putText(frame, f"Gesture: {alphabet_var.get()}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    video_label.imgtk = img
    video_label.configure(image=img)
    
    root.after(10, process)

process()
root.protocol("WM_DELETE_WINDOW", lambda: [cap.release(), root.destroy()])
root.mainloop()
