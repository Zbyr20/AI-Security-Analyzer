# 🔒 AI-Security-Analyzer

An intelligent web security scanner that leverages AI to analyze and report security vulnerabilities. This application combines multiple security scanning techniques with AI-powered analysis to provide comprehensive security assessments.

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Features](#features)
- [Known Issues](#known-issues)
- [Development](#development)
- [License](#license)

## 📌 Overview

AI-Security-Analyzer is a full-stack web application that performs automated security scanning on websites and generates AI-powered security reports. It combines traditional security scanning methods with modern AI analysis to identify and document security vulnerabilities.

### Key Features:
- 🌐 Multiple security scanning methods (SSL, TLS, DNS, Headers, Cookies, Ports)
- 🤖 AI-powered vulnerability analysis using Qwen3 model
- 💻 User-friendly React frontend
- ⚡ Fast API backend
- 📊 Detailed security reports

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI 0.141.1
- **Language**: Python 3.x
- **Validation**: Pydantic
- **HTTP Client**: OpenAI Python client
- **Server**: Uvicorn

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite
- **Styling**: CSS3
- **Linting**: ESLint

### AI & Infrastructure
- **AI Model**: Qwen3-4b-cuda-gpu
- **Model Access**: Foundry API (localhost:51054)

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Port 5173)               │
│                   - URL Input Component                     │
│                   - Results Display                         │
│                   - Report Visualization                    │
└────────────────────┬────────────────────────────────────────┘
                     │ (HTTP REST)
┌────────────────────▼────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                │
│  ┌─────────────────────────────────────────────────────────┤
│  │ API Routes                                              │
│  │ ├── POST /scan - Main security scanning endpoint       │
│  │ └── GET /health - Health check                         │
│  └─────────────────────────────────────────────────────────┤
│                     │                                       │
│  ┌──────────────────┴──────────────────────────────────┐  │
│  │ Security Scanner Components                        │  │
│  ├── SSL Scanner                                      │  │
│  ├── TLS Scanner                                      │  │
│  ├── DNS Scanner                                      │  │
│  ├── Header Scanner                                   │  │
│  ├── Cookie Scanner                                   │  │
│  └── Port Scanner                                     │  │
│                     │                                       │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │ AI Service (Qwen3 Integration)                      │  │
│  │ - Report Generation                                 │  │
│  │ - Vulnerability Analysis                            │  │
│  └──────────────────┬──────────────────────────────────┘  │
└─────────────────────┼──────────────────────────────────────┘
                      │ (OpenAI Python Client)
┌─────────────────────▼──────────────────────────────────────┐
│     Foundry API (Qwen3 Model)                              │
│     http://127.0.0.1:51054/v1                              │
└────────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm or yarn** (package manager)
- **Foundry** running locally with Qwen3-4b-cuda-gpu model on port 51054

### Optional but Recommended:
- **Virtual Environment Tool** (venv, virtualenv, or conda)
- **Git** (for version control)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI-Security-Analyzer
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## ▶️ Running the Application

### Prerequisites Check
Ensure Foundry is running with Qwen3 model:
```bash
# Foundry should be accessible at http://127.0.0.1:51054/v1
```

### Start Backend

```bash
cd backend

# Activate virtual environment (if not already activated)
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Start the FastAPI server
python -m uvicorn app.main:app --reload
```

The backend will be available at: **http://127.0.0.1:8000**

### Start Frontend (New Terminal)

```bash
cd frontend
npm run dev
```

The frontend will be available at: **http://127.0.0.1:5173**

### Access the Application

Open your browser and navigate to:
```
http://127.0.0.1:5173
```

## 📁 Project Structure

```
AI-Security-Analyzer/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Configuration settings
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   └── ai_service.py         # Qwen3 AI integration
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py             # API endpoints
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── security_result.py    # Data models
│   │   ├── prompts/
│   │   │   └── security_prompt.py    # AI prompts
│   │   ├── scanner/
│   │   │   ├── __init__.py
│   │   │   ├── security_scanner.py   # Main scanner orchestrator
│   │   │   ├── ssl_scanner.py        # SSL/TLS certificate checks
│   │   │   ├── tls_scanner.py        # TLS version checks
│   │   │   ├── dns_scanner.py        # DNS records checks
│   │   │   ├── header_scanner.py     # HTTP headers security checks
│   │   │   ├── cookie_scanner.py     # Cookie security checks
│   │   │   ├── port_scanner.py       # Open ports detection
│   │   │   └── models.py             # Scanner data models
│   │   └── validators/
│   │       └── url_validator.py      # URL validation logic
│   ├── requirements.txt              # Python dependencies
│   └── .venv/                        # Virtual environment (created on setup)
│
├── frontend/                         # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx                   # Main React component
│   │   ├── App.css                   # Application styles
│   │   ├── index.css                 # Global styles
│   │   ├── main.jsx                  # Entry point
│   │   └── assets/                   # Static assets
│   ├── public/                       # Public static files
│   ├── package.json                  # NPM dependencies
│   ├── vite.config.js                # Vite configuration
│   ├── eslint.config.js              # ESLint configuration
│   └── index.html                    # HTML template
│
└── README.md                         # This file
```

## 📡 API Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Security Scan
```http
POST /scan
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Request Parameters:**
- `url` (string, required): The website URL to scan

**Response:**
```json
{
  "url": "https://example.com",
  "scan_timestamp": "2024-01-15T10:30:00Z",
  "security_checks": {
    "ssl": { ... },
    "tls": { ... },
    "dns": { ... },
    "headers": { ... },
    "cookies": { ... },
    "ports": { ... }
  },
  "ai_analysis": "Detailed AI-powered security report...",
  "summary": "Overall security assessment..."
}
```

## ✨ Features

### Security Scanning
- ✅ **SSL/TLS Certificate Analysis** - Validates certificate validity, expiration, and chain
- ✅ **TLS Version Detection** - Identifies supported TLS versions
- ✅ **DNS Records Scan** - Analyzes DNS configuration for security issues
- ✅ **HTTP Headers Analysis** - Checks for missing security headers
- ✅ **Cookie Security** - Validates cookie flags and attributes
- ✅ **Port Scanning** - Detects open ports and running services

### AI Analysis
- 🤖 Qwen3-powered vulnerability assessment
- 📊 Detailed security reports with recommendations
- 🔍 Pattern recognition for common vulnerabilities

### User Interface
- 🎨 Clean, intuitive React-based frontend
- ⚡ Real-time scanning feedback
- 📱 Responsive design

## ⚠️ Known Issues

1. **Missing Implementations**
   - `generate_security_report()` method in AIService needs completion
   - DNS Scanner implementation file missing
   - Cookie Scanner implementation file missing

2. **Technical Limitations**
   - SSL Scanner may experience connection issues with some domains
   - Limited error handling and recovery mechanisms
   - CORS policy limited to localhost:5173 only

3. **Infrastructure**
   - No logging system implemented
   - Missing health check monitoring
   - No timeout/retry mechanisms for external API calls

4. **Documentation**
   - Missing API documentation/Swagger UI
   - No inline code comments for complex logic
   - Missing deployment documentation

## 🔧 Development

### Code Style
- Follow Python PEP 8 guidelines for backend code
- Follow ESLint configuration for frontend code
- Use meaningful variable and function names

### Adding New Scanners
1. Create a new scanner class in `backend/app/scanner/`
2. Inherit from base scanner pattern
3. Implement `scan()` method
4. Integrate into `SecurityScanner` orchestrator

### Frontend Development
- Use React hooks for state management
- Follow component-based architecture
- Keep components modular and reusable

### Testing
```bash
# Backend testing (when test suite is available)
cd backend
pytest

# Frontend testing (when test suite is available)
cd frontend
npm test
```

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version (must be 3.8+)
python --version
```

### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check Node version (must be 16+)
node --version
```

### Qwen3 Model Connection Issues
```bash
# Verify Foundry is running
curl http://127.0.0.1:51054/v1/models

# Check firewall/port availability
netstat -an | grep 51054
```

### CORS Errors
- Ensure frontend is running on `localhost:5173`
- Backend CORS is configured for this address only
- To allow other origins, modify `CORS_ORIGINS` in `backend/app/config.py`

## 📝 License

[Add your license information here]

## 👥 Contributing

Contributions are welcome! Please feel free to:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues, questions, or suggestions, please open an issue on the repository.

---

**Last Updated:** August 29, 2024
**Status:** In Development
