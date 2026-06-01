import json
import os
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Header, Depends, status
from fastapi.responses import HTMLResponse
import bcrypt

# Initializing application
app = FastAPI(title="Agent Education System")

# Password hashing configuration - using bcrypt directly

# Path to local user store
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# In-memory storage fallback and sessions
users_db: Dict[str, str] = {}  # email -> hashed_password
sessions_db: Dict[str, str] = {}  # token -> email

# Load users from JSON on startup
if os.path.exists(USERS_FILE):
    try:
        with open(USERS_FILE, "r") as f:
            users_db = json.load(f)
    except Exception:
        users_db = {}

def save_users():
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users_db, f)
    except Exception:
        pass

# Mock Courses Data (Strictly including corporate & academic modules as per specification)
COURSES = {
    "corporate-tesco": {
        "id": "corporate-tesco",
        "title": "Tesco Operational Standards",
        "category": "Corporate",
        "badge": "Corporate Training",
        "description": "Learn the official Tesco operating principles, checkout standards, and customer service compliance regulations.",
        "lessons": [
            {
                "id": "tesco-values",
                "title": "1. Tesco Core Values & Customer Promise",
                "content": "At Tesco, our core values are: 'No one tries harder for customers' and 'We treat people how they want to be treated'. Customer service standards require active listening, quick checkout processing, and polite greetings. This lesson covers standard service phrases and compliance rules."
            },
            {
                "id": "tesco-checkout",
                "title": "2. Checkout Scanning Standards (Interactive Simulator)",
                "content": "To maintain checkout speed and item handling standards, you must scan items efficiently. Items must be scanned with the barcode facing the sensor, fragile items (like bread and eggs) must be handled with care, and heavy items must not be double-lifted. Complete the Checkout Simulator below to demonstrate your skills."
            }
        ]
    },
    "academic-ai": {
        "id": "academic-ai",
        "title": "Introduction to Artificial Intelligence",
        "category": "Academic",
        "badge": "Academic Module",
        "description": "Explore the fundamentals of Artificial Intelligence, Machine Learning algorithms, and neural network training processes.",
        "lessons": [
            {
                "id": "ai-history",
                "title": "1. The History and Core Concepts of AI",
                "content": "Artificial Intelligence (AI) refers to the simulation of human intelligence processes by machines. We track its history from Alan Turing's Turing Test in 1950, the Dartmouth workshop in 1956, to modern deep learning models. Key concepts include symbolic AI, heuristic search, and representative learning."
            },
            {
                "id": "ai-sandbox",
                "title": "2. Interactive Machine Learning Sandbox",
                "content": "Machine learning involves optimization techniques to fit models to historical data. In this sandbox, you will adjust model training parameters: Learning Rate and Training Epochs. Run the interactive simulation to see how a model learns to fit linear data points and reduce loss."
            }
        ]
    }
}

# Pydantic Schemas
class RegisterSchema(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

class LoginSchema(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str

class UserResponse(BaseModel):
    email: str
    message: str

class LoginResponse(BaseModel):
    session_token: str
    email: str
    message: str

# Authentication Helper
def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid session token",
        )
    token = authorization.split(" ")[1]
    if token not in sessions_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid",
        )
    return sessions_db[token]

# --- Auth Endpoints ---

@app.post("/api/register", response_model=UserResponse)
def register(user: RegisterSchema):
    if user.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )
    
    # Hash password using bcrypt
    hashed_pwd = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    users_db[user.email] = hashed_pwd
    save_users()
    
    return {"email": user.email, "message": "Student account registered successfully"}

@app.post("/api/login", response_model=LoginResponse)
def login(credentials: LoginSchema):
    hashed_pwd = users_db.get(credentials.email)
    if not hashed_pwd or not bcrypt.checkpw(credentials.password.encode('utf-8'), hashed_pwd.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create session token
    session_token = str(uuid.uuid4())
    sessions_db[session_token] = credentials.email
    
    return {
        "session_token": session_token,
        "email": credentials.email,
        "message": "Login successful"
    }

# --- Course Endpoints ---

@app.get("/api/courses")
def list_courses(current_user: str = Depends(get_current_user)):
    # Return brief info about courses
    return [
        {
            "id": c["id"],
            "title": c["title"],
            "category": c["category"],
            "badge": c["badge"],
            "description": c["description"]
        }
        for c in COURSES.values()
    ]

@app.get("/api/courses/{course_id}")
def view_course(course_id: str, current_user: str = Depends(get_current_user)):
    if course_id not in COURSES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return COURSES[course_id]

# --- Server Frontend UI (HTMLResponse) ---
@app.get("/", response_class=HTMLResponse)
def get_home():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Education System</title>
    <style>
        /* Modern Glassmorphic Design System (Strictly Offline, No Google Fonts or External calls) */
        :root {
            --bg-gradient: linear-gradient(135deg, #0b071e, #130d2a);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-shadow: rgba(0, 0, 0, 0.4);
            --text-color: #e2e8f0;
            --text-muted: #94a3b8;
            --primary: #818cf8;
            --primary-hover: #4f46e5;
            --accent: #2dd4bf;
            --accent-hover: #14b8a6;
            --card-hover-bg: rgba(255, 255, 255, 0.08);
            --error: #ef4444;
            --success: #10b981;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Glassmorphic Navigation */
        header {
            background: rgba(15, 10, 35, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--glass-border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .logo {
            font-size: 1.4rem;
            font-weight: 700;
            background: linear-gradient(to right, var(--primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .nav-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .user-badge {
            font-size: 0.85rem;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.05);
            padding: 0.4rem 0.8rem;
            border-radius: 50px;
            border: 1px solid var(--glass-border);
        }

        .btn {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(129, 140, 248, 0.2);
        }

        .btn:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
        }

        .btn-outline {
            background: transparent;
            border: 1px solid var(--glass-border);
            color: var(--text-color);
            box-shadow: none;
        }

        .btn-outline:hover {
            background: var(--glass-bg);
            border-color: var(--text-muted);
        }

        .btn-accent {
            background: var(--accent);
            color: #0b071e;
            box-shadow: 0 4px 12px rgba(45, 212, 191, 0.2);
        }

        .btn-accent:hover {
            background: var(--accent-hover);
        }

        .container {
            max-width: 1200px;
            width: 100%;
            margin: 2rem auto;
            padding: 0 1.5rem;
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        /* Views (Sign in / Register) */
        .auth-card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 2.5rem;
            max-width: 450px;
            width: 100%;
            margin: 4rem auto;
            box-shadow: 0 8px 32px var(--glass-shadow);
        }

        .auth-card h2 {
            margin-bottom: 1.5rem;
            text-align: center;
            font-size: 1.8rem;
        }

        .form-group {
            margin-bottom: 1.2rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        .form-control {
            width: 100%;
            padding: 0.8rem;
            border-radius: 8px;
            border: 1px solid var(--glass-border);
            background: rgba(0, 0, 0, 0.2);
            color: white;
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        .form-control:focus {
            border-color: var(--primary);
            outline: none;
        }

        .auth-toggle {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.9rem;
            color: var(--text-muted);
        }

        .auth-toggle a {
            color: var(--primary);
            text-decoration: none;
            font-weight: 600;
        }

        .auth-toggle a:hover {
            text-decoration: underline;
        }

        .alert {
            padding: 0.8rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            display: none;
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--error);
            color: #fca5a5;
            display: block;
        }

        .alert-success {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid var(--success);
            color: #a7f3d0;
            display: block;
        }

        /* Dashboard & Courses Grid */
        .dashboard-header {
            margin-bottom: 2rem;
        }

        .dashboard-header h1 {
            font-size: 2.2rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .courses-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1.5rem;
        }

        .course-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.8rem;
            transition: all 0.3s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .course-card:hover {
            transform: translateY(-5px);
            background: var(--card-hover-bg);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            border-color: rgba(255,255,255,0.15);
        }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 1rem;
            width: fit-content;
        }

        .badge-corporate {
            background: rgba(45, 212, 191, 0.15);
            color: var(--accent);
            border: 1px solid rgba(45, 212, 191, 0.3);
        }

        .badge-academic {
            background: rgba(129, 140, 248, 0.15);
            color: var(--primary);
            border: 1px solid rgba(129, 140, 248, 0.3);
        }

        .course-card h3 {
            font-size: 1.3rem;
            margin-bottom: 0.8rem;
            color: white;
        }

        .course-card p {
            color: var(--text-muted);
            font-size: 0.95rem;
            line-height: 1.5;
            flex-grow: 1;
            margin-bottom: 1.5rem;
        }

        .course-card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            border-top: 1px solid var(--glass-border);
            padding-top: 1rem;
        }

        /* Course Viewer Split Screen Layout */
        .course-viewer {
            display: grid;
            grid-template-columns: 280px 1fr;
            gap: 2rem;
            flex: 1;
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 1.5rem;
            min-height: 500px;
        }

        .back-nav {
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.95rem;
            transition: color 0.2s;
        }

        .back-nav:hover {
            color: white;
        }

        .sidebar {
            border-right: 1px solid var(--glass-border);
            padding-right: 1rem;
        }

        .sidebar h4 {
            font-size: 1rem;
            color: var(--text-muted);
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .lesson-list {
            list-style: none;
        }

        .lesson-item {
            padding: 0.8rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            color: var(--text-muted);
            border: 1px solid transparent;
        }

        .lesson-item:hover {
            background: rgba(255, 255, 255, 0.03);
            color: white;
        }

        .lesson-item.active {
            background: var(--glass-bg);
            color: var(--primary);
            border-color: var(--glass-border);
            font-weight: 600;
        }

        .lesson-content {
            padding: 0 1rem;
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .lesson-content h2 {
            font-size: 1.8rem;
            margin-bottom: 1.2rem;
            color: white;
        }

        .lesson-text {
            font-size: 1.05rem;
            line-height: 1.65;
            color: var(--text-color);
            margin-bottom: 2.5rem;
        }

        /* Custom Interactive Simulator Widgets */
        .simulator-box {
            background: rgba(0, 0, 0, 0.25);
            border: 1px dashed var(--glass-border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 1.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .simulator-header {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Tesco Simulator Specific styles */
        .tesco-simulation {
            width: 100%;
            max-width: 500px;
            text-align: center;
        }

        .tesco-scanner-target {
            background: #1e1b4b;
            border: 2px solid var(--accent);
            border-radius: 12px;
            padding: 2rem;
            margin: 1.5rem 0;
            position: relative;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            box-shadow: inset 0 0 20px rgba(45, 212, 191, 0.2);
        }

        .red-laser {
            width: 100%;
            height: 2px;
            background: var(--error);
            box-shadow: 0 0 8px var(--error);
            position: absolute;
            top: 50%;
            left: 0;
            animation: scanLaser 2s infinite ease-in-out;
        }

        @keyframes scanLaser {
            0%, 100% { top: 15%; }
            50% { top: 85%; }
        }

        .scan-item-label {
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
            z-index: 10;
        }

        .barcode-graphic {
            width: 140px;
            height: 45px;
            background: repeating-linear-gradient(90deg, #fff, #fff 4px, #000 4px, #000 8px);
            margin-top: 10px;
            z-index: 10;
            border: 2px solid white;
        }

        .tesco-stats {
            display: flex;
            justify-content: space-around;
            width: 100%;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--glass-border);
        }

        .stat-item {
            text-align: center;
        }

        .stat-val {
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--accent);
        }

        .stat-lbl {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        /* AI Simulator Specific styles */
        .ai-simulation {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
        }

        .ai-controls {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            justify-content: center;
            width: 100%;
        }

        .control-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .control-group label {
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .control-group select, .control-group input {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--glass-border);
            color: white;
            padding: 0.5rem;
            border-radius: 6px;
            width: 120px;
        }

        .ai-plot-canvas {
            background: #090615;
            border: 1px solid var(--glass-border);
            border-radius: 8px;
            width: 100%;
            max-width: 480px;
            height: 240px;
        }

        .loss-badge {
            font-family: monospace;
            background: rgba(255,255,255,0.06);
            padding: 0.4rem 1rem;
            border-radius: 4px;
            border: 1px solid var(--glass-border);
        }

        /* Hide details initially */
        #main-dashboard, #course-viewer-section {
            display: none;
        }
    </style>
</head>
<body>

    <!-- Header Navigation -->
    <header>
        <div class="logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="color: var(--primary)"><path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path></svg>
            Agent Education System
        </div>
        <div class="nav-actions" id="nav-actions">
            <!-- Populated dynamically via JS -->
        </div>
    </header>

    <!-- Main Container -->
    <div class="container">

        <!-- AUTH: Login View -->
        <div id="auth-login" class="auth-card">
            <h2>Student Login</h2>
            <div id="login-alert" class="alert alert-error" style="display:none;"></div>
            <form id="login-form">
                <div class="form-group">
                    <label for="login-email">Email Address</label>
                    <input type="email" id="login-email" class="form-control" placeholder="student@example.com" required autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="login-password">Password</label>
                    <input type="password" id="login-password" class="form-control" placeholder="••••••••" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn" style="width: 100%; margin-top: 1rem;">Log In</button>
            </form>
            <div class="auth-toggle">
                New student? <a href="#" onclick="toggleAuthView('register')">Create an account</a>
            </div>
        </div>

        <!-- AUTH: Register View -->
        <div id="auth-register" class="auth-card" style="display:none;">
            <h2>Student Registration</h2>
            <div id="register-alert" class="alert alert-error" style="display:none;"></div>
            <form id="register-form">
                <div class="form-group">
                    <label for="register-email">Email Address</label>
                    <input type="email" id="register-email" class="form-control" placeholder="student@example.com" required autocomplete="email">
                </div>
                <div class="form-group">
                    <label for="register-password">Password (min 6 characters)</label>
                    <input type="password" id="register-password" class="form-control" placeholder="••••••••" required minlength="6" autocomplete="new-password">
                </div>
                <button type="submit" class="btn btn-accent" style="width: 100%; margin-top: 1rem;">Register Student</button>
            </form>
            <div class="auth-toggle">
                Already registered? <a href="#" onclick="toggleAuthView('login')">Log in</a>
            </div>
        </div>

        <!-- MAIN: Courses Dashboard -->
        <div id="main-dashboard">
            <div class="dashboard-header">
                <h1>Welcome Back to Learning</h1>
                <p style="color: var(--text-muted)">Select a training module to proceed with your coursework.</p>
            </div>
            <div class="courses-grid" id="courses-grid">
                <!-- Courses list cards injected dynamically here -->
            </div>
        </div>

        <!-- VIEW: Course Viewer -->
        <div id="course-viewer-section">
            <div class="back-nav" onclick="showDashboard()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                Back to Dashboard
            </div>
            <div class="course-viewer">
                <div class="sidebar">
                    <h4 id="sidebar-course-title">Training Modules</h4>
                    <ul class="lesson-list" id="lesson-list">
                        <!-- Lesson navigation links injected here -->
                    </ul>
                </div>
                <div class="lesson-content">
                    <h2 id="lesson-title">Lesson Title</h2>
                    <div class="lesson-text" id="lesson-text">
                        Lesson details go here.
                    </div>
                    <!-- Placeholders for Interactive Simulators -->
                    <div id="tesco-sim-container" style="display:none; width: 100%;">
                        <div class="simulator-box">
                            <div class="simulator-header">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"></rect><line x1="12" y1="4" x2="12" y2="20"></line></svg>
                                Tesco Scanner Terminal
                            </div>
                            <div class="tesco-simulation">
                                <p style="color: var(--text-muted); margin-bottom: 1rem;">Scan food items by matching the barcode orientation guidelines.</p>
                                <div class="tesco-scanner-target">
                                    <div class="red-laser"></div>
                                    <div class="scan-item-label" id="tesco-item-name">Tesco Fresh Organic Milk</div>
                                    <div class="barcode-graphic"></div>
                                </div>
                                <div style="display:flex; gap:1rem; justify-content:center;">
                                    <button class="btn btn-accent" id="tesco-scan-btn" onclick="simulateTescoScan()">Scan Item</button>
                                </div>
                                <div class="tesco-stats">
                                    <div class="stat-item">
                                        <div class="stat-val" id="tesco-scanned-count">0 / 5</div>
                                        <div class="stat-lbl">Items Scanned</div>
                                    </div>
                                    <div class="stat-item">
                                        <div class="stat-val" id="tesco-accuracy">100%</div>
                                        <div class="stat-lbl">Scanning Accuracy</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="ai-sim-container" style="display:none; width: 100%;">
                        <div class="simulator-box">
                            <div class="simulator-header">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                                AI Network Optimization Sandbox
                            </div>
                            <div class="ai-simulation">
                                <div class="ai-controls">
                                    <div class="control-group">
                                        <label for="ai-lr">Learning Rate</label>
                                        <select id="ai-lr">
                                            <option value="0.1">0.1 (Fast)</option>
                                            <option value="0.01" selected>0.01 (Medium)</option>
                                            <option value="0.001">0.001 (Slow)</option>
                                        </select>
                                    </div>
                                    <div class="control-group">
                                        <label for="ai-epochs">Training Epochs</label>
                                        <select id="ai-epochs">
                                            <option value="50">50 Epochs</option>
                                            <option value="100" selected>100 Epochs</option>
                                            <option value="200">200 Epochs</option>
                                        </select>
                                    </div>
                                    <div style="display:flex; align-items:flex-end;">
                                        <button class="btn btn-accent" id="ai-train-btn" onclick="startAITraining()">Train Model</button>
                                    </div>
                                </div>
                                <canvas class="ai-plot-canvas" id="ai-canvas" width="480" height="240"></canvas>
                                <div class="loss-badge">
                                    Training Loss: <span id="ai-loss" style="color:var(--accent)">1.2045</span>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>

    </div>

    <!-- Frontend logic -->
    <script>
        let sessionToken = localStorage.getItem("session_token");
        let userEmail = localStorage.getItem("user_email");
        let currentCourses = [];
        let selectedCourse = null;

        // Tesco simulator variables
        let tescoScanned = 0;
        const tescoItems = [
            "Tesco Fresh Organic Milk",
            "Tesco Finest Wood Fired Pizza",
            "Tesco Soft Wholemeal Bread",
            "Tesco Extra Virgin Olive Oil",
            "Tesco British Free Range Eggs"
        ];

        // AI simulator variables
        let trainingInterval = null;

        window.onload = function() {
            if (sessionToken) {
                showDashboard();
            } else {
                toggleAuthView("login");
            }
        };

        function setAlert(id, type, message) {
            const el = document.getElementById(id);
            if (!message) {
                el.style.display = "none";
                return;
            }
            el.className = `alert alert-${type}`;
            el.innerText = message;
            el.style.display = "block";
        }

        function toggleAuthView(view) {
            setAlert("login-alert", "error", "");
            setAlert("register-alert", "error", "");
            if (view === "login") {
                document.getElementById("auth-login").style.display = "block";
                document.getElementById("auth-register").style.display = "none";
                document.getElementById("main-dashboard").style.display = "none";
                document.getElementById("course-viewer-section").style.display = "none";
            } else {
                document.getElementById("auth-login").style.display = "none";
                document.getElementById("auth-register").style.display = "block";
                document.getElementById("main-dashboard").style.display = "none";
                document.getElementById("course-viewer-section").style.display = "none";
            }
            updateHeader();
        }

        function updateHeader() {
            const navActions = document.getElementById("nav-actions");
            if (sessionToken) {
                navActions.innerHTML = `
                    <span class="user-badge">${userEmail}</span>
                    <button class="btn btn-outline" onclick="logout()">Logout</button>
                `;
            } else {
                navActions.innerHTML = `
                    <button class="btn btn-outline" onclick="toggleAuthView('login')">Login</button>
                `;
            }
        }

        // Register Student Action
        document.getElementById("register-form").onsubmit = async function(e) {
            e.preventDefault();
            setAlert("register-alert", "error", "");
            const email = document.getElementById("register-email").value;
            const password = document.getElementById("register-password").value;

            try {
                const response = await fetch("/api/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    toggleAuthView("login");
                    setAlert("login-alert", "success", "Registration successful. Please log in.");
                } else {
                    setAlert("register-alert", "error", data.detail || "Registration failed");
                }
            } catch (err) {
                setAlert("register-alert", "error", "Failed to connect to authentication server");
            }
        };

        // Login Student Action
        document.getElementById("login-form").onsubmit = async function(e) {
            e.preventDefault();
            setAlert("login-alert", "error", "");
            const email = document.getElementById("login-email").value;
            const password = document.getElementById("login-password").value;

            try {
                const response = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    sessionToken = data.session_token;
                    userEmail = data.email;
                    localStorage.setItem("session_token", sessionToken);
                    localStorage.setItem("user_email", userEmail);
                    showDashboard();
                } else {
                    setAlert("login-alert", "error", data.detail || "Login failed");
                }
            } catch (err) {
                setAlert("login-alert", "error", "Failed to connect to authentication server");
            }
        };

        function logout() {
            localStorage.clear();
            sessionToken = null;
            userEmail = null;
            toggleAuthView("login");
        }

        // Load Course Catalog List
        async function showDashboard() {
            setAlert("login-alert", "error", "");
            document.getElementById("auth-login").style.display = "none";
            document.getElementById("auth-register").style.display = "none";
            document.getElementById("course-viewer-section").style.display = "none";
            document.getElementById("main-dashboard").style.display = "block";
            updateHeader();

            try {
                const response = await fetch("/api/courses", {
                    headers: { "Authorization": `Bearer ${sessionToken}` }
                });
                if (response.ok) {
                    currentCourses = await response.json();
                    renderCourses(currentCourses);
                } else {
                    // Session expired
                    logout();
                }
            } catch (err) {
                console.error("Error listing courses:", err);
            }
        }

        function renderCourses(courses) {
            const grid = document.getElementById("courses-grid");
            grid.innerHTML = "";
            courses.forEach(course => {
                const isCorporate = course.category === "Corporate";
                const badgeClass = isCorporate ? "badge-corporate" : "badge-academic";
                
                const card = document.createElement("div");
                card.className = "course-card";
                card.onclick = () => loadCourse(course.id);
                card.innerHTML = `
                    <span class="badge ${badgeClass}">${course.badge}</span>
                    <h3>${course.title}</h3>
                    <p>${course.description}</p>
                    <div class="course-card-footer">
                        <span>Modules: 2 Units</span>
                        <span style="color:var(--accent)">Start Training →</span>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        // Load Course detail & lessons
        async function loadCourse(courseId) {
            try {
                const response = await fetch(`/api/courses/${courseId}`, {
                    headers: { "Authorization": `Bearer ${sessionToken}` }
                });
                if (response.ok) {
                    selectedCourse = await response.json();
                    openCourseViewer();
                }
            } catch (err) {
                console.error("Error loading course details", err);
            }
        }

        function openCourseViewer() {
            document.getElementById("main-dashboard").style.display = "none";
            document.getElementById("course-viewer-section").style.display = "block";
            document.getElementById("sidebar-course-title").innerText = selectedCourse.title;

            const list = document.getElementById("lesson-list");
            list.innerHTML = "";
            selectedCourse.lessons.forEach((lesson, index) => {
                const item = document.createElement("li");
                item.className = `lesson-item ${index === 0 ? 'active' : ''}`;
                item.innerText = lesson.title;
                item.onclick = () => selectLesson(lesson, item);
                list.appendChild(item);
            });

            // Select first lesson by default
            selectLesson(selectedCourse.lessons[0], list.firstChild);
        }

        function selectLesson(lesson, element) {
            // Update active sidebar selection
            document.querySelectorAll(".lesson-item").forEach(item => item.classList.remove("active"));
            if (element) element.classList.add("active");

            // Display Title & Text
            document.getElementById("lesson-title").innerText = lesson.title;
            document.getElementById("lesson-text").innerText = lesson.content;

            // Hide/Show interactive elements
            document.getElementById("tesco-sim-container").style.display = "none";
            document.getElementById("ai-sim-container").style.display = "none";

            if (lesson.id === "tesco-checkout") {
                document.getElementById("tesco-sim-container").style.display = "block";
                resetTescoSimulator();
            } else if (lesson.id === "ai-sandbox") {
                document.getElementById("ai-sim-container").style.display = "block";
                resetAISimulator();
            }
        }

        // --- Mock Corporate Module (Tesco) Logic ---
        function resetTescoSimulator() {
            tescoScanned = 0;
            document.getElementById("tesco-scanned-count").innerText = `${tescoScanned} / 5`;
            document.getElementById("tesco-item-name").innerText = tescoItems[0];
            document.getElementById("tesco-accuracy").innerText = "100%";
            document.getElementById("tesco-scan-btn").disabled = false;
            document.getElementById("tesco-scan-btn").innerText = "Scan Item";
        }

        function simulateTescoScan() {
            if (tescoScanned < 5) {
                tescoScanned++;
                document.getElementById("tesco-scanned-count").innerText = `${tescoScanned} / 5`;
                
                // Add accuracy deviation for visual interest
                const acc = Math.floor(92 + Math.random() * 8);
                document.getElementById("tesco-accuracy").innerText = `${acc}%`;

                if (tescoScanned < 5) {
                    document.getElementById("tesco-item-name").innerText = tescoItems[tescoScanned];
                } else {
                    document.getElementById("tesco-item-name").innerText = "Training Module Completed! ✅";
                    document.getElementById("tesco-scan-btn").disabled = true;
                    document.getElementById("tesco-scan-btn").innerText = "Course Unit Complete";
                }
            }
        }

        // --- Mock Academic Module (AI) Logic ---
        function resetAISimulator() {
            if (trainingInterval) clearInterval(trainingInterval);
            document.getElementById("ai-train-btn").disabled = false;
            document.getElementById("ai-train-btn").innerText = "Train Model";
            document.getElementById("ai-loss").innerText = "1.2045";
            
            // Draw baseline static scatter plot and initial bad line
            drawAIPlot(0, 0);
        }

        function startAITraining() {
            const lr = parseFloat(document.getElementById("ai-lr").value);
            const epochs = parseInt(document.getElementById("ai-epochs").value);
            
            document.getElementById("ai-train-btn").disabled = true;
            document.getElementById("ai-train-btn").innerText = "Training...";

            let currentEpoch = 0;
            let loss = 1.2045;
            
            if (trainingInterval) clearInterval(trainingInterval);

            // Simulation step
            trainingInterval = setInterval(() => {
                currentEpoch += 2;
                // Loss decreases asymptotically
                loss = (1.2045 / (1 + (currentEpoch * lr * 4))).toFixed(4);
                document.getElementById("ai-loss").innerText = loss;

                // Animate fitting coefficient
                const progress = currentEpoch / epochs;
                drawAIPlot(progress, loss);

                if (currentEpoch >= epochs) {
                    clearInterval(trainingInterval);
                    document.getElementById("ai-train-btn").innerText = "Model Trained! ✅";
                    document.getElementById("ai-loss").innerText = `${loss} (Done)`;
                }
            }, 30);
        }

        function drawAIPlot(progress, currentLoss) {
            const canvas = document.getElementById("ai-canvas");
            if (!canvas) return;
            const ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Set grid styling
            ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
            ctx.lineWidth = 1;
            for(let x=40; x<canvas.width; x+=40) {
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
            }
            for(let y=40; y<canvas.height; y+=40) {
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }

            // Draw Scatter data points
            const dataPoints = [
                {x: 60, y: 190}, {x: 100, y: 170}, {x: 140, y: 150},
                {x: 180, y: 135}, {x: 220, y: 120}, {x: 260, y: 95},
                {x: 300, y: 90}, {x: 340, y: 70}, {x: 380, y: 55}, {x: 420, y: 40}
            ];

            ctx.fillStyle = "rgba(45, 212, 191, 0.7)";
            dataPoints.forEach(pt => {
                ctx.beginPath();
                ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
                ctx.fill();
            });

            // Model fitting regression line
            // Initial line is flat y=200. Ideal line goes from x=40,y=200 to x=440,y=35.
            const startY = 200 - (160 * progress);
            const endY = 200 - (165 * progress);

            ctx.strokeStyle = "rgba(129, 140, 248, 0.95)";
            ctx.lineWidth = 3;
            ctx.shadowBlur = 8;
            ctx.shadowColor = "rgba(129, 140, 248, 0.5)";
            
            ctx.beginPath();
            ctx.moveTo(40, startY);
            ctx.lineTo(440, endY);
            ctx.stroke();
            
            // reset shadow
            ctx.shadowBlur = 0;
        }
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
