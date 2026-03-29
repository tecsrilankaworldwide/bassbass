# Grade 5 Scholarship Examination Platform

**Education Reforms Bureau** - Digital Examination System  
**Domain:** educationreforms.cloud  
**Tech Stack:** FastAPI (Python), React (JavaScript), MongoDB Atlas

---

## 🎓 Overview

Comprehensive digital examination platform for Grade 2-5 students in Sri Lanka, featuring:

- **MCQ Exams (Paper 1):** 60-question exams with auto-grading and 60-minute timer
- **Paper 2 Marking:** Manual marking for essay and short answer questions
- **Skill Tracking:** Performance across 10 skill areas with detailed analytics
- **Progress Reports:** Monthly charts and trends for parents
- **Multi-language Support:** Sinhala, Tamil, English
- **PDF Exam System:** Upload and manage PDF-based exams
- **Role-based Access:** Student, Teacher, Parent, Admin, Typesetter

---

## 🌟 Features

### For Students
- Take timed MCQ exams with autosave
- Resume exams if connection drops
- View instant results with skill breakdown
- Question navigator and flag system
- Mobile-friendly exam interface

### For Teachers
- Create 60-question MCQ exams
- Assign skill areas to questions
- Publish exams to students
- Mark Paper 2 (essay + 10 short answers)
- View student performance

### For Parents
- Monthly progress dashboard
- Skill radar charts
- Strengths/weaknesses analysis
- Historical trends

### For Admins
- User management (create, edit users)
- View system statistics
- Manage all grades and exams

### For Typesetters
- Create PDF-based exams
- Upload PDFs in 3 languages (si/ta/en)
- Manage exam content

---

## 🏗️ Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- MongoDB (Atlas M10+)
- JWT Authentication
- Async I/O for high concurrency

**Frontend:**
- React 18
- React Router for navigation
- Recharts for data visualization
- Tailwind CSS + shadcn/ui
- i18next for multi-language

**Infrastructure:**
- DigitalOcean Droplet (8GB RAM recommended)
- MongoDB Atlas (Singapore region)
- Nginx reverse proxy
- PM2 process manager
- Let's Encrypt SSL

---

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Yarn package manager

### 1. Clone Repository

```bash
git clone https://github.com/tecsrilankaworldwide/grade5-scholarship-exam.git
cd grade5-scholarship-exam
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env
nano .env  # Edit with your MongoDB URL and secret key

# Run backend
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

**Backend .env variables:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME_EXAM=exam_bureau_db
SECRET_KEY=your-secret-key-min-32-chars
CORS_ORIGINS=http://localhost:3000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Create .env file
cp .env.example .env
nano .env  # Edit with backend URL

# Run frontend
yarn start
```

**Frontend .env variables:**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 4. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api/
- API Docs: http://localhost:8001/api/docs

---

## 🔑 Test Credentials

Sample users are auto-created on first backend startup:

- **Student:** student@test.com / student123
- **Teacher:** teacher@test.com / teacher123
- **Parent:** parent@test.com / parent123
- **Admin:** admin@test.com / admin123

---

## 📦 Production Deployment

See **[DIGITALOCEAN_DEPLOYMENT.md](./DIGITALOCEAN_DEPLOYMENT.md)** for comprehensive production deployment guide.

**Quick Summary:**
1. Prepare DigitalOcean droplet (Ubuntu 22.04+)
2. Install Node.js, Python 3.11, nginx, PM2
3. Set up MongoDB Atlas M10+ cluster
4. Clone repository and configure .env files
5. Build frontend: `yarn build`
6. Start backend with PM2
7. Configure nginx with SSL (Let's Encrypt)
8. Done! 🎉

**Docker Deployment (Alternative):**
```bash
docker-compose up -d
```

See [docker-compose.yml](./docker-compose.yml) for configuration.

---

## 🎯 10 Skill Areas Tracked

1. Mathematical Reasoning
2. Language Proficiency
3. General Knowledge
4. Comprehension Skills
5. Problem Solving
6. Logical Thinking
7. Spatial Reasoning
8. Memory & Recall
9. Analytical Skills
10. Critical Thinking

---

## 📂 Project Structure

```
.
├── backend/                 # FastAPI backend
│   ├── server.py           # Main application
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment template
│   └── uploads/            # PDF uploads (gitignored)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── components/    # Reusable components
│   │   ├── i18n/          # Translations
│   │   └── App.js         # Main app
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment template
├── docker-compose.yml     # Docker setup
├── DIGITALOCEAN_DEPLOYMENT.md  # Deployment guide
└── README.md              # This file
```

---

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- CORS protection
- Rate limiting on API endpoints
- SQL injection prevention (using MongoDB)
- XSS protection headers

**Important:** Never commit `.env` files! Always use `.env.example` templates.

---

## 🌐 API Endpoints

**Authentication:**
- `POST /api/register` - Register new user
- `POST /api/login` - Login user

**Exams:**
- `GET /api/exams` - List exams
- `POST /api/exams/create` - Create exam (teacher)
- `POST /api/exams/{id}/start` - Start exam (student)
- `POST /api/attempts/{id}/save` - Save answer
- `POST /api/attempts/{id}/submit` - Submit exam
- `PUT /api/exams/{id}/publish` - Publish exam

**Progress:**
- `GET /api/students/{id}/progress` - Get student progress

**Paper 2:**
- `POST /api/paper2/submit-meta` - Submit Paper 2 metadata
- `PUT /api/paper2/{id}/mark` - Mark Paper 2 (teacher)

**PDF Exams:**
- `POST /api/exams/create-pdf` - Create PDF exam
- `POST /api/exams/{id}/upload-pdf/{lang}` - Upload PDF
- `GET /api/exams/{id}/pdf/{lang}` - Get PDF

Full API documentation: http://localhost:8001/api/docs

---

## 📊 Performance

**Optimized for 1000+ concurrent users:**
- MongoDB connection pooling (100 connections)
- In-memory caching with TTLCache
- Async/await for non-blocking I/O
- Nginx rate limiting and caching
- Frontend code splitting
- Static asset caching (1 year)

**Recommended Server Specs:**
- CPU: 4 vCPUs
- RAM: 8 GB
- Disk: 160 GB SSD
- MongoDB: Atlas M10 (Singapore region)

---

## 🌍 Multi-language Support

Supported languages:
- **Sinhala (si)** - සිංහල
- **Tamil (ta)** - தமிழ்
- **English (en)**

Translations managed via i18next. Language switcher available on all pages.

---

## 🧪 Testing

Backend tests:
```bash
cd backend
source venv/bin/activate
pytest backend_test.py
```

Frontend tests:
```bash
cd frontend
yarn test
```

---

## 📝 License

Proprietary - © 2026 TEC Sri Lanka Worldwide (Pvt.) Ltd

All rights reserved. This software is for use by Education Reforms Bureau only.

---

## 🤝 Contact

**Education Reforms Bureau**  
Established: 1982  
Website: www.tecaikids.com  
Email: info@educationreforms.cloud

---

## 🙏 Acknowledgments

- Built for Sri Lankan students preparing for Grade 5 Scholarship Exams
- Serving grades 2-5 with comprehensive skill tracking
- Designed for 1000+ concurrent users
- Developed with ❤️ for the future of education

---

**Version:** 2.0.0  
**Last Updated:** February 2026  
**Status:** Production Ready ✅
