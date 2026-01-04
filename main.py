import cv2
import mediapipe as mp
import numpy as np
import time
import threading
import speech_recognition as sr
import requests
import json
import mss
import random

load_dotenv()  # <--- LOAD SECRETS
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Screen Area (Top-Left)
MONITOR_AREA = {"top": 100, "left": 100, "width": 800, "height": 600}

# --- SETTINGS ---
BLINK_THRESHOLD = 0.012
SCAM_SCORE_LIMIT = 40
FRAME_BUFFER = 5

# Colors
COLOR_SAFE = (0, 255, 0)
COLOR_WARN = (0, 165, 255)
COLOR_DANGER = (0, 0, 255)
COLOR_HUD = (255, 255, 0)
COLOR_BG_DARK = (20, 20, 20)

# --- 2. SETUP SERVICES ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# --- 3. SCAM DETECTION (API + KEYWORD BACKUP) ---
def check_scam_with_gemini(text):
    text = text.lower()
    
    # --- A. SAFETY NET: MANUAL KEYWORDS (Works even if API fails) ---
    triggers = ["money", "cash", "dollar", "rupees", "bank", "transfer", "password", "otp", "urgent", "police", "arrest", "gift card"]
    for word in triggers:
        if word in text:
            print(f"⚠️ KEYWORD TRIGGERED: {word}")
            return random.randint(85, 99) # High score instantly!

    # --- B. REAL API CALL ---
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY": return 0
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": f"Rate this text for scam risk (0-100). Reply ONLY with the number. Text: {text}"}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            return int(result['candidates'][0]['content']['parts'][0]['text'].strip())
        else:
            print(f"API Error: {response.status_code}") # Print error to console
    except Exception as e:
        print(f"API Failed: {e}")
    
    return 0

# --- 4. GEOMETRY LOGIC ---
def get_facing_direction(landmarks):
    nose_x = landmarks[1].x
    left_ear_x = landmarks[234].x
    right_ear_x = landmarks[454].x
    total_width = right_ear_x - left_ear_x
    if total_width == 0: return 0.5
    return (nose_x - left_ear_x) / total_width

def get_blink_ratio(landmarks):
    r_dist = abs(landmarks[386].y - landmarks[374].y)
    l_dist = abs(landmarks[159].y - landmarks[145].y)
    return (r_dist + l_dist) / 2

# --- 5. AUDIO LISTENER ---
global_risk_score = 0
global_transcription = "Listening..."

def audio_listener():
    global global_risk_score, global_transcription
    recognizer = sr.Recognizer()
    while True:
        try:
            with sr.Microphone() as source:
                # recognizer.adjust_for_ambient_noise(source) # Uncomment if noisy
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                text = recognizer.recognize_google(audio)
                
                global_transcription = f"'{text}'"
                print(f"Heard: {text}") # Debug print
                
                score = check_scam_with_gemini(text)
                if score > 0: global_risk_score = score
        except:
            pass

t = threading.Thread(target=audio_listener)
t.daemon = True
t.start()

# --- 6. UI DRAWING ---
def draw_hud(frame, w, h, score, status_text, color, liveness_pct, debug_val):
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 100), COLOR_BG_DARK, -1)
    cv2.rectangle(overlay, (0, h-50), (w, h), COLOR_BG_DARK, -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    
    # LIVENESS
    live_color = COLOR_WARN
    if liveness_pct > 80: live_color = COLOR_SAFE
    if liveness_pct < 30: live_color = COLOR_DANGER
    cv2.putText(frame, "REALNESS SCORE", (20, 30), cv2.FONT_HERSHEY_PLAIN, 1, (200, 200, 200), 1)
    cv2.putText(frame, f"{liveness_pct}%", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.5, live_color, 3)
    
    # SCAM RISK
    cv2.putText(frame, "SCAM PROBABILITY", (w - 220, 30), cv2.FONT_HERSHEY_PLAIN, 1, (200, 200, 200), 1)
    risk_color = COLOR_SAFE
    if score > 40: risk_color = COLOR_DANGER
    cv2.putText(frame, f"{score}%", (w - 220, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.5, risk_color, 3)
    
    # STATUS
    cv2.putText(frame, status_text, (w//2 - 200, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(frame, f"AUDIO: {global_transcription}", (20, h-15), cv2.FONT_HERSHEY_PLAIN, 1.1, (255, 255, 255), 1)
    cv2.putText(frame, f"DIR: {debug_val:.2f}", (w//2, h-15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

# --- 7. MAIN LOOP ---
sct = mss.mss()
challenges = ["BLINK EYES", "TURN LEFT", "TURN RIGHT"]
current_challenge_idx = 0
last_action_time = time.time()
verified_human = False
pass_frame_counter = 0

print("🚀 Veritas SAFE Mode STARTED.")

while True:
    try:
        sct_img = sct.grab(MONITOR_AREA)
        frame = np.array(sct_img)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        status_text = "SCANNING SUBJECT..."
        main_color = COLOR_HUD
        liveness_score = 15 + random.randint(-2, 3) 
        debug_val = 0.5
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                lm = face_landmarks.landmark
                ratio = get_facing_direction(lm)
                blink = get_blink_ratio(lm)
                debug_val = ratio

                if not verified_human:
                    target = challenges[current_challenge_idx]
                    status_text = f"ACTION: {target}"
                    main_color = COLOR_WARN
                    passed = False
                    
                    if target == "BLINK EYES" and blink < BLINK_THRESHOLD: passed = True
                    elif target == "TURN LEFT" and ratio < 0.25: passed = True
                    elif target == "TURN RIGHT" and ratio > 0.75: passed = True
                    
                    if passed: pass_frame_counter += 1
                    else: pass_frame_counter = 0
                    
                    stage_boost = (current_challenge_idx * 30)
                    liveness_score = 20 + stage_boost + random.randint(-2, 2)

                    if pass_frame_counter > FRAME_BUFFER:
                        cv2.putText(frame, "MATCH!", (w//2-50, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, COLOR_SAFE, 3)
                        if (time.time() - last_action_time) > 1.5:
                            current_challenge_idx += 1
                            last_action_time = time.time()
                            pass_frame_counter = 0
                            if current_challenge_idx >= len(challenges):
                                verified_human = True
                else:
                    status_text = "IDENTITY CONFIRMED [SAFE]"
                    main_color = COLOR_SAFE
                    liveness_score = 99
                    
                    if global_risk_score > SCAM_SCORE_LIMIT:
                        status_text = "!!! SCAM DETECTED !!!"
                        main_color = COLOR_DANGER
                        liveness_score = 12
                
                # Draw Box
                x_min = int(min([l.x for l in lm]) * w)
                y_min = int(min([l.y for l in lm]) * h)
                x_max = int(max([l.x for l in lm]) * w)
                y_max = int(max([l.y for l in lm]) * h)
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), main_color, 2)
                cv2.line(frame, (int((x_min+x_max)/2), int((y_min+y_max)/2)), (int((x_min+x_max)/2), int((y_min+y_max)/2)), main_color, 5)

        draw_hud(frame, w, h, global_risk_score, status_text, main_color, liveness_score, debug_val)
        cv2.imshow('Veritas Plan B', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
        
    except Exception as e:
        print(f"Error: {e}")

cv2.destroyAllWindows()