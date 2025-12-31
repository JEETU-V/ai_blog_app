AI Blog Generator
📖 Project Description
An intelligent web application that transforms YouTube videos into well-structured blog posts using AI. The application downloads video audio, transcribes it using AssemblyAI, and generates engaging blog content automatically.

✨ Features
🤖 AI-Powered Blog Generation
Convert YouTube videos to blog posts in seconds

Uses AssemblyAI for accurate transcription

Smart content structuring and formatting

Supports all YouTube links (videos, shorts, live streams)

🎨 Modern User Interface
Beautiful, responsive design with Tailwind CSS

Glassmorphism effects and gradients

Dark mode elements throughout

Smooth animations and transitions

Mobile-friendly responsive design

📊 Dashboard & Analytics
Real-time statistics dashboard

Monthly blog generation tracking

Word count analytics

Recent blog history

Visual progress indicators

🔐 User Management
Secure user authentication (login/signup)

Profile management

Blog history per user

Protected routes and sessions

📝 Blog Management
View all generated blogs

Detailed blog view with statistics

Copy, share, and export functionality

Search and filter blogs

Sort by date, title, or popularity

🛠️ Tech Stack
Backend
Django - Python web framework

Django REST Framework - API endpoints

SQLite/PostgreSQL - Database

AssemblyAI - Audio transcription

yt-dlp - YouTube audio download

Gunicorn - Production server

Frontend
HTML5/CSS3 - Structure and styling

Tailwind CSS - Utility-first CSS framework

JavaScript (ES6+) - Interactive features

Font Awesome - Icons

Vanilla JavaScript - No framework bloat

APIs & Services
AssemblyAI API - Audio transcription

YouTube Data - Video metadata

Custom Django REST API - Blog management

📁 Project Structure
text
ai_blog_app/
├── backend/
│   ├── ai_blog_app/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── blog_generator/
│   │   ├── migrations/
│   │   ├── templates/
│   │   │   ├── index.html          # Main dashboard
│   │   │   ├── login.html          # Login page
│   │   │   ├── signup.html         # Signup page
│   │   │   ├── all-blogs.html      # Blog listing
│   │   │   └── blog-details.html   # Blog details
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py              # BlogPost model
│   │   ├── urls.py               # App URLs
│   │   ├── views.py              # All views and logic
│   │   └── tests.py
│   ├── media/                    # Uploaded files
│   ├── static/                   # Static files
│   ├── requirements.txt          # Python dependencies
│   └── manage.py                # Django management
└── README.md                    # This file
⚙️ Installation
Prerequisites
Python 3.8+

pip (Python package manager)

Virtual environment (recommended)

Step-by-Step Setup
Clone the repository

bash
git clone <repository-url>
cd ai_blog_app/backend
Create virtual environment

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies

bash
pip install -r requirements.txt
Configure environment variables
Create a .env file in the backend directory:

env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# AssemblyAI
ASSEMBLYAI_API_KEY=your-assemblyai-api-key

# Database (optional - SQLite default)
DATABASE_URL=sqlite:///db.sqlite3
Apply migrations

bash
python manage.py makemigrations
python manage.py migrate
Create superuser (optional)

bash
python manage.py createsuperuser
Collect static files

bash
python manage.py collectstatic
Run development server

bash
python manage.py runserver
Visit http://127.0.0.1:8000 in your browser.
