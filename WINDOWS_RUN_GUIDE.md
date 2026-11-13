# JAL AI - Windows Run Guide

This guide provides exact commands to run the JAL AI project on Windows.

## Prerequisites

- Python 3.10 or newer (tested with Python 3.13)
- Node.js 20 or newer with npm
- Git (optional)

## Project Structure

```
hmwssb agent/
├── backend/          # FastAPI Python backend
│   ├── app/         # Application modules
│   ├── .env         # Environment variables (create from .env.example)
│   └── .venv/       # Python virtual environment
├── frontend/        # Next.js React frontend
│   ├── app/         # Next.js app directory
│   ├── components/  # React components
│   └── .env.local   # Environment variables (create from .env.local.example)
└── tests/           # Python test files
```

## Initial Setup (One-time)

### 1. Setup Backend

Open PowerShell in the project directory and run:

```powershell
# Navigate to backend directory
cd "C:\Users\Abhi\Downloads\hmwssb agent\backend"

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Create .env file from example
Copy-Item .env.example .env

# Edit .env and set your demo OTP (default is 123456)
# The file should contain:
# DEMO_MODE=1
# DEMO_OTP=123456
# CORS_ORIGINS=http://localhost:3000
# SESSION_TTL_SECONDS=1800
```

### 2. Setup Frontend

Open a new PowerShell window:

```powershell
# Navigate to frontend directory
cd "C:\Users\Abhi\Downloads\hmwssb agent\frontend"

# Install dependencies
npm install

# Create .env.local file
# The file should contain:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Start Backend (Terminal 1)

```powershell
cd "C:\Users\Abhi\Downloads\hmwssb agent\backend"
.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

Backend will start on: http://localhost:8000

Verify health endpoint: http://localhost:8000/health
API documentation: http://localhost:8000/docs

### Start Frontend (Terminal 2)

```powershell
cd "C:\Users\Abhi\Downloads\hmwssb agent\frontend"
npm run dev
```

Frontend will start on: http://localhost:3000

## Running Tests

```powershell
cd "C:\Users\Abhi\Downloads\hmwssb agent\backend"
.venv\Scripts\Activate.ps1
python -m pytest ../tests/test_core.py ../tests/test_voice_assistant.py -v
```

Expected: 22 tests passed

## Sign In

1. Open http://localhost:3000 in your browser
2. Click "Get Started" or "Sign In"
3. Enter any 10-digit mobile number (e.g., 9876543210)
4. Enter the demo OTP configured in backend/.env (default: 123456)
5. You will be redirected to the dashboard

## Available Features

### Dashboard Pages
- Overview - Quick stats and navigation
- Assistant - Chat and voice interface
- Bills - Bill intelligence, variance, anomalies, forecast
- History - Complete billing history table
- Rebates - Rebate analysis
- Tanker - Tanker booking request form
- Tanker Tracking - Booking status (empty in guided mode)
- Grievances - Grievance filing form
- Grievance Tracking - Grievance status (empty in guided mode)
- Info - Official HMWSSB contact information
- Analytics - Billing charts and trends
- Account - Account management and logout

### Demo OTP
Default: 123456 (configured in backend/.env)

### Environment Variables

**Backend (.env):**
- `DEMO_MODE=1` - Enable demo mode
- `DEMO_OTP=123456` - Demo OTP code
- `CORS_ORIGINS=http://localhost:3000` - Allowed CORS origins
- `SESSION_TTL_SECONDS=1800` - Session timeout

**Frontend (.env.local):**
- `NEXT_PUBLIC_API_URL=http://localhost:8000` - Backend API URL

## Stopping the Servers

In each terminal window, press `Ctrl+C` to stop the server.

## Troubleshooting

### Backend fails to start with "DEMO_OTP not set"
- Ensure backend/.env exists and contains DEMO_OTP
- Restart the backend server

### Frontend shows connection errors
- Ensure backend is running on port 8000
- Check frontend/.env.local has correct NEXT_PUBLIC_API_URL
- Check browser console for CORS errors

### Python installation errors
- Ensure Python 3.10+ is installed and in PATH
- Try using `py` launcher instead of `python`

### npm install fails
- Ensure Node.js 20+ is installed
- Delete node_modules and package-lock.json, then run npm install again

## Important Notes

- This is an **unofficial demo service** for educational purposes
- All data shown is **demo data** (marked with "Demo data" badges)
- Tanker bookings and grievance filings are in **guided mode** - nothing is actually submitted
- For official HMWSSB services, visit https://www.hmwssb.gov.in
- Browser speech recognition may send audio to the browser vendor's service
- Session data is stored in memory and lost on server restart

## Project Status

### Implemented
- ✅ Backend: FastAPI with all API endpoints
- ✅ Backend: Deterministic billing engine with Decimal math
- ✅ Backend: Anomaly detection and forecasting
- ✅ Backend: Voice assistant with wake word, flows, OTP rejection
- ✅ Backend: Tool allowlist and security invariants
- ✅ Frontend: Next.js with TypeScript and Tailwind CSS
- ✅ Frontend: All 12 dashboard pages
- ✅ Frontend: Billing charts with Recharts
- ✅ Frontend: Sign-in flow with demo OTP
- ✅ Frontend: API client with proper error handling
- ✅ Tests: 22 Python tests passing

### Partial / Future Work
- ⚠️ Cinematic landing page: Basic version implemented, full Canvas 2D animation pending
- ⚠️ Voice client: Basic implementation in assistant page, full Web Speech integration pending
- ⚠️ Accessibility: Basic keyboard navigation, full ARIA labels pending
- ❌ HMWSSB integration: Not authorized (guided mode only)
- ❌ Database: In-memory stores only (PostgreSQL pending)
- ❌ LLM integration: Rule-based routing only (LLM pending)

## Support

For issues or questions, check the BUILD_SPEC.md and CINEMATIC_PLAN.md documents in the project.
