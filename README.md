# 🚗 Automated Number Plate Recognition (ANPR) with Vehicle Log Management

An intelligent system that automatically detects vehicle number plates from images or videos, extracts the registration number using OCR, and stores structured vehicle logs with real-time monitoring and management features.

---

## 📌 Project Overview

The **Automated Number Plate Recognition (ANPR) System** is designed to replace manual vehicle monitoring with an efficient, accurate, and automated solution.

It uses:

* **YOLOv8** for object detection (vehicles & number plates)
* **EasyOCR** for text extraction
* **Django** for backend and dashboard
* **OpenCV** for image/video processing

The system supports both:

* 🎥 Real-time video streaming
* 📁 Uploaded video processing

---

## 🎯 Features

* 🚘 Vehicle Detection using YOLOv8
* 🔍 Number Plate Recognition (OCR)
* 🧾 Automatic Vehicle Log Storage
* 📊 Web Dashboard (Django आधारित UI)
* ⚠️ Blacklist / Whitelist Detection
* 🔎 Search & Filter Vehicle Records
* 📂 CSV Export Support
* 📡 Real-time Video Processing
* 🖼️ Cropped & Processed Plate Images

---

## 🧠 Tech Stack

| Category         | Technology           |
| ---------------- | -------------------- |
| Programming      | Python 3.10+         |
| Computer Vision  | OpenCV               |
| Object Detection | YOLOv8               |
| OCR              | EasyOCR              |
| Backend          | Django               |
| Database         | SQLite / MySQL       |
| Frontend         | HTML, CSS, Bootstrap |

---

## ⚙️ System Workflow

1. Capture video/image input
2. Detect vehicles using YOLOv8
3. Locate number plate
4. Preprocess image (grayscale, thresholding)
5. Extract text using OCR
6. Validate plate format
7. Store data in database
8. Display results on dashboard

---

## 📂 Project Structure
```
ANPR/
│
├── ANPRLMS/                 **# Main Django Project Folder**
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── ml/                      **# Machine Learning Modules**
│   ├── detector.py
│   ├── realtime.py
│   ├── video_processing.py  **# Video upload processing**
│   ├── util.py
│   └── models/              **# YOLO Weights**
│       ├── best.pt
│       └── yolov8s.pt
│
├── admin_panel/             **# Admin Dashboard**
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── admin_panel/
│
├── guard_panel/             **# Guard Dashboard**
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── guard_panel/
│
├── myapp/                   **# Authentication (Signup/Login)**
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── myapp/
│           ├── signup.html
│           ├── login.html
│           └── home.html
│
├── static/                  **# CSS, JS, Images**
│
├── media/                   **# Uploaded images/videos**
│
├── output/                  **# Detection Results**
│   └── cars/                **# Saved vehicle images**
│       ├── sample1.jpg
│       └── sample2.jpg
│
├── manage.py
├── requirements.txt
└── README.md
```
---
## Project Screenshots
Link - https://drive.google.com/drive/folders/10xMNdhKLIMLBzHNBn5DmxcUH2GL8KlYF

---
---
## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository

<pre class="overflow-visible! px-0!" data-start="2127" data-end="2212"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span class="ͼl">git</span><span> clone https://github.com/your-username/ANPR-System.git</span><br/><span class="ͼl">cd</span><span> ANPR-System</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

### 2️⃣ Install Dependencies

<pre class="overflow-visible! px-0!" data-start="2243" data-end="2286"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>pip install </span><span class="ͼn">-r</span><span> requirements.txt</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

### 3️⃣ Apply Migrations

<pre class="overflow-visible! px-0!" data-start="2313" data-end="2381"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>python manage.py makemigrations</span><br/><span>python manage.py migrate</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

### 4️⃣ Create Admin User (Optional)

<pre class="overflow-visible! px-0!" data-start="2420" data-end="2464"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>python manage.py createsuperuser</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

### 5️⃣ Run Server

<pre class="overflow-visible! px-0!" data-start="2485" data-end="2523"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute inset-x-4 top-12 bottom-4"><div class="pointer-events-none sticky z-40 shrink-0 z-1!"><div class="sticky bg-token-border-light"></div></div></div><div class="relative"><div class=""><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>python manage.py runserver</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

👉 Open browser:

<pre class="overflow-visible! px-0!" data-start="2542" data-end="2572"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>http://127.0.0.1:8000/</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

---

## ▶️ How to Use

### 🔹 Real-Time Detection

* Start video stream
* System detects and logs vehicles automatically

### 🔹 Video Upload

* Upload a recorded video
* Process and view results with detected plates

### 🔹 Dashboard

* View vehicle logs
* Search by plate number
* Manage blacklist/whitelist

---

## 📊 Performance

* 🎯 Detection Accuracy: ~90%
* 🔤 OCR Accuracy: ~83%
* ⚡ Real-time capable with GPU

---

## 📁 Output

### CSV Format

<pre class="overflow-visible! px-0!" data-start="3038" data-end="3101"><div class="relative w-full mt-4 mb-1"><div class=""><div class="relative"><div class="h-full min-h-0 min-w-0"><div class="h-full min-h-0 min-w-0"><div class="border border-token-border-light border-radius-3xl corner-superellipse/1.1 rounded-3xl"><div class="h-full w-full border-radius-3xl bg-token-bg-elevated-secondary corner-superellipse/1.1 overflow-clip rounded-3xl lxnfua_clipPathFallback"><div class="pointer-events-none absolute end-1.5 top-1 z-2 md:end-2 md:top-1"></div><div class="relative"><div class="pe-11 pt-3"><div class="relative z-0 flex max-w-full"><div id="code-block-viewer" dir="ltr" class="q9tKkq_viewer cm-editor z-10 light:cm-light dark:cm-light flex h-full w-full flex-col items-stretch ͼd ͼr"><div class="cm-scroller"><pre class="cm-content q9tKkq_readonly m-0"><code><span>time,license_number,confidence</span><br/><span>12:01:05,UP32AB1234,0.92</span></code></pre></div></div></div></div></div></div></div></div></div><div class=""><div class=""></div></div></div></div></div></pre>

### Stored Data

* Plate Number
* Timestamp
* Confidence Score
* Vehicle Status (Blacklist/Whitelist)
* Captured Image

---

## 🚧 Challenges Faced

* OCR errors in low lighting
* Motion blur issues
* Duplicate detections
* Real-time performance without GPU

---

## 🔮 Future Improvements

* 🚀 Improve OCR accuracy (custom model)
* ☁️ Cloud deployment
* 📱 Mobile app integration
* 🔔 Real-time alerts (SMS/Email)
* 🎥 Multi-camera support
* 🌍 Support multiple plate formats

---

## 👩‍💻 Contributors

* **Nancy Gaur**
* **Abhinav Sharma**

---

## 📜 License

This project is for academic and educational purposes.

---

## 🙌 Acknowledgements

* YOLOv8 – Ultralytics
* OpenCV
* EasyOCR
* Django Framework
* Roboflow Dataset
