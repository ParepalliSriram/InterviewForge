# 🐸 InterviewFroge: AI-First Interview Preparation Platform

InterviewFroge is a premium, AI-first interview preparation web application. It allows candidates to generate custom mock interview sessions tailored to their target role, experience level, and optionally, their resume contents. The platform leverages advanced LLM APIs to conduct and grade sessions, offering real-time custom feedback, candidate analytics, and recommended study paths.

---

## 🚀 Key Features

*   **Custom Mock Interviews**: Generates five tailored questions based on job title, experience, and interview type (Technical, Behavioral, Mixed).
*   **Resume Integration**: Parses resumes to contextualize and personalize mock interview questions.
*   **Multi-Model AI Support**: Fully modular provider system supports:
    *   **Google Gemini** (via `google-generativeai`)
    *   **OpenAI** (via `openai`)
    *   **Anthropic Claude** (via `anthropic`)
    *   **Groq AI** (via Groq Cloud SDK)
*   **Intelligent Auto-Fallback**: If the primary AI provider experiences an outage or rate limits, the application automatically switches to available fallback models.
*   **Granular Performance Evaluation**: Grades technical depth and problem-solving metrics, returning strengths, weaknesses, and a consolidated score report.
*   **Detailed Analytics Dashboard**: Tracks overall averages, best scores, topic-by-topic analytics, and generates dynamic recommendations.
*   **Modern SPA Frontend**: Interactive UI built using vanilla CSS & JS, featuring responsiveness, dynamic dark/light mode toggles, and seamless animations.

---

## 🛠️ Technology Stack

### Backend
*   **FastAPI**: High-performance Python web framework for build APIs.
*   **MongoDB & Motor**: Asynchronous MongoDB database connector.
*   **Pydantic (v2)**: Data validation and settings management.
*   **Starlette Sessions**: Signed-cookie based session management.
*   **Bcrypt & Passlib**: Secure password hashing for user accounts.

### Frontend
*   **Vanilla CSS**: Custom styling optimized for dark/light themes, card layouts, and responsiveness.
*   **Vanilla JavaScript**: Interactive SPA logic handling state, authentication flow, dynamically updating dashboards, and real-time interview state.

---

## 📂 Project Directory Structure

```text
InterviewForge/
├── app/
│   ├── routes/                # API route handlers
│   │   ├── auth.py            # User registration, login, logout, and profile updates
│   │   ├── dashboard.py       # Metrics, activity logs, and recommendation builders
│   │   └── interview.py       # Session generation, answer evaluation, and analytics persistence
│   ├── services/
│   │   ├── ai/                # AI Provider implementation
│   │   │   ├── base_provider.py
│   │   │   ├── claude_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   ├── groq_provider.py
│   │   │   ├── openai_provider.py
│   │   │   └── provider_manager.py
│   │   └── resume.py          # Local resume parsing and parsing summary extraction
│   ├── static/                # Single Page Application Frontend
│   │   ├── css/               # Modular stylesheet rules
│   │   ├── js/                # Client-side routing and layout rendering logic
│   │   └── index.html         # Main app entrypoint
│   ├── auth.py                # Security, hashing, and dependency helpers
│   ├── config.py              # Configuration loading via pydantic-settings
│   ├── database.py            # Database client and startup lifespans
│   ├── main.py                # App setup and route middleware configuration
│   └── models.py              # Pydantic validation schemas
├── .env.example               # Template for environment configurations
├── requirements.txt           # Python application dependencies
└── README.md                  # Project documentation (this file)
```

---

## ⚙️ Setup and Installation

### 1. Prerequisites
Ensure you have the following installed on your system:
*   [Python 3.8+](https://www.python.org/downloads/)
*   [MongoDB](https://www.mongodb.com/try/download/community) (either a running local instance or a MongoDB Atlas URI)

### 2. Installation
Clone the repository and navigate to the root directory:

```bash
git clone <repository-url>
cd InterviewForge
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to a new file named `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in the configuration details. You must provide at least one AI provider key:

```ini
# MongoDB connection settings
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=interview_froge

# Session signing secret key
SECRET_KEY=supersecretkey_interview_froge_123!

# AI Provider Configurations
# Options: gemini, openai, claude, groq
PRIMARY_PROVIDER=groq

# Provider API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
CLAUDE_API_KEY=your_claude_api_key
GROQ_API_KEY=your_groq_api_key
```

---

## 🏃 Running the Application

To start the FastAPI server locally:

```bash
uvicorn app.main:app --reload
```

Once started, the application will run at:
*   **Web Application (Frontend)**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
*   **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔌 API Endpoints Summary

### Authentication (`/api/auth`)
*   `POST /register` - Register a new user account.
*   `POST /login` - Log in and initialize a secure session.
*   `POST /logout` - Log out and clear current session cookies.
*   `GET /me` - Retrieve current user authentication status and profile information.
*   `POST /update-username` - Update the authenticated user's profile username.

### Mock Interview (`/api/interview`)
*   `POST /setup` - Prepares the session, extracts resume context, and fetches generated AI questions.
*   `POST /submit` - Submits the answers, scores them, and persists analytics if user is authenticated.

### Analytics Dashboard (`/api/dashboard`)
*   `GET /summary` - Generates high-level metrics (averages, strong/weak areas, topic attempts, aggregated recommendations).
*   `GET /history` - Fetches the full historical record of completed mock interviews with full grading reports.
