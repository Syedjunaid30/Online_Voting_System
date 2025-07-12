# 🗳️ Online Voting System with Face Recognition

A secure, user-friendly Online Voting System built with Python Flask and face recognition. Users can register with face verification, cast one-time votes, and view real-time live results. Admin can manage parties and voters, and reset the entire system.

---

## 🚀 Features

- ✅ User registration with face image
- ✅ Password strength validation
- ✅ Face duplication check (via encoding & distance threshold)
- ✅ One-time secure vote casting
- ✅ Real-time live vote results (with Chart.js)
- ✅ Admin panel for:
  - Adding parties
  - Viewing voter info
  - Live result chart
  - System reset
- ✅ Generates a PDF report of results
- ✅ Session-secured access for users and admin

---

## 🛠️ Technologies Used

- Python 3.8
- Flask (Backend)
- face_recognition + dlib (Face Verification)
- MySQL (Database)
- Chart.js (Live Result Chart)
- HTML5 + CSS3 + JS (Frontend)
- ReportLab (PDF generation)

---

## 💻 Local Setup Instructions (XAMPP + MySQL)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/online-voting-system.git
cd online-voting-system
```

---
### 2️⃣ Set Up Python Virtual Environment

```bash
python3 -m venv env
source env/bin/activate
```
---

### 3️⃣ Install Python Dependencies
```bash
pip install -r requirements.txt
```
If you’re on Windows and installing face_recognition fails, see the note below.
---

### 4️⃣ Set Up MySQL Database using XAMPP
1. Launch XAMPP, start Apache and MySQL

2. Go to http://localhost/phpmyadmin

3. Create a database called:
```bash
voting_system
```
4. Import the file voting_system.sql (provided in the repo):

- Click on the Import tab
- Choose voting_system.sql
- Click Go

✅ This creates all tables:

- users
- votes
- parties
- admins

---
🔐 Admin Account
✅ Admin registration is not provided in the UI to prevent unauthorized access.

The system auto-creates the admin on reset:

Username: `Admin`
Password: `admin@123`

📌 You can also insert it manually with this SQL:

```bash
INSERT INTO admins (id, username, password)
VALUES (1, 'admin', 'admin@123');
```
---

## 🎥 Face Recognition Setup (for face_recognition + dlib)
On macOS:
```bash
brew install cmake boost
pip install dlib face_recognition
```
---
On Windows:
Download Visual Studio Build Tools:
👉 https://visualstudio.microsoft.com/visual-cpp-build-tools/

During install, select:

✔ "C++ build tools"

✔ "Windows 10 SDK"

✔ "CMake tools for Windows"

Then run:
```bash
pip install cmake
pip install dlib face_recognition
```
### ▶️ Run the Application
```bash
python app.py
```
---
## 📁 Project Structure
```bash
online-voting-system/
├── app.py
├── voting_system.sql
├── requirements.txt
├── README.md
├── templates/
│   ├── register.html
│   ├── login.html
│   └── ...
├── static/
│   ├── css/
│   ├── js/
│   ├── videos/
│   ├── face_data/
│   └── party_logos/
└── .gitignore
```
---
## 📷 Screenrecording: It's in the folder of Demo Screenrecording.

---
📃 License
MIT License

---
### 🙏 Credits
- Flask
- face_recognition
- Chart.js
- ReportLab
- XAMPP
