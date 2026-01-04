# 🛡️ VeritasStream
### Real-Time Deepfake Defense & Scam Prevention System

**VeritasStream** is an AI-powered security layer for video calls. It acts as a "Firewall for Human Connection," analyzing video feeds in real-time to detect deepfakes, AI face swaps, and financial scam attempts before they cause harm.

Built for **[Insert Hackathon Name]**.

![Demo Screenshot](image_f5dc5e.jpg)
*(Replace this link with your actual screenshot url if needed)*

---

## 🚀 Key Features

### 👁️ Active Liveness Forensics
Veritas uses a "Challenge-Response" protocol (Simon Says) to verify humanity.
* **Geometric Analysis:** Calculates strict nose-to-ear ratios to detect 2D video injection.
* **Action Challenges:** Users must "Blink", "Turn Left", or "Turn Right" to prove they are not a pre-recorded loop.
* **Realness Score:** A dynamic confidence meter (0-100%) that updates as the user passes biometric checks.

### 🔊 Audio Scam Shield
* **Real-Time Transcription:** Listens to the call audio and converts speech to text on the fly.
* **Keyword Traps:** Instantly triggers a **RED ALERT** if high-risk words ("Transfer", "Money", "OTP", "Police") are detected.
* **AI Context Analysis:** Uses **Google Gemini 1.5 Flash** to analyze complex sentences for social engineering patterns.

### 💻 Cyberpunk HUD
* A non-intrusive, forensics-style overlay that sits on top of any video call app (Zoom, WhatsApp, Meet).
* Displays live telemetry: Yaw angles, scam probability, and real-time subtitles.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11
* **Vision:** OpenCV, MediaPipe (Face Mesh)
* **Audio:** SpeechRecognition, PyAudio
* **Screen Capture:** MSS (High-speed screen grabbing)
* **AI Intelligence:** Google Gemini API (via raw REST requests)

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/VeritasStream.git](https://github.com/YOUR_USERNAME/VeritasStream.git)
cd VeritasStream
