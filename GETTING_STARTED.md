# 🚀 Sentinel - Getting Started Guide

## What is Sentinel?

Sentinel is a **memory-driven threat detection system** that uses AI and vector embeddings to detect Advanced Persistent Threats (APTs) by correlating subtle anomalies across months of network activity.

Think of it as a security guard with perfect memory - it remembers every suspicious event and can connect patterns that appear benign individually but indicate compromise when viewed together.

---

## ⚡ 5-Minute Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### Step 2: Configure (Optional)
```bash
cp .env.example .env
# Edit .env with your credentials if you have them
# Demo works without any credentials!
```

### Step 3: Start Services (3 Terminals)

**Terminal 1 - Backend API**
```bash
python local_server.py
```
✓ Wait for: `Server running on http://localhost:8000`

**Terminal 2 - Frontend Dashboard**
```bash
cd frontend && npm start
```
✓ Browser opens at `http://localhost:3000`

**Terminal 3 - Run Demo**
```bash
python auto_demo.py
```
✓ Watch the dashboard update with 5 threats over 20 seconds

---

## 📁 Important Files & What They Do

### Core Application
| File | Purpose |
|------|---------|
| `local_server.py` | Main API server (runs on 8000) |
| `frontend/src/App.js` | React dashboard |
| `src/sentinel_agent.py` | Main threat detection logic |
| `src/embedding_service.py` | Vector embeddings for AI |
| `src/database.py` | CockroachDB connection |

### Demo & Testing
| File | Purpose |
|------|---------|
| `auto_demo.py` | ⭐ **5-event demo** (use for video) |
| `demo_mode.py` | Interactive attack scenarios |
| `run_200_tests.py` | 200 comprehensive test cases |
| `load_test_100_users.py` | Performance testing with 100 users |
| `postman_collection.json` | API testing collection |

### Documentation
| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `QUICK_DEMO_SCRIPT.md` | 2-minute demo narration |
| `DEMO_VIDEO_GUIDE.md` | Full video production guide |
| `VIDEO_DEMO_READINESS.md` | Pre-recording checklist |
| `PUSH_SUMMARY.md` | What was recently pushed |
| `ARCHITECTURE.md` | Technical deep dive |

---

## 🎬 For Video Demos

### Option 1: Automated Demo (Recommended)
```bash
python auto_demo.py
```
**What**: 5 automatically simulated threats over 20 seconds  
**Best for**: Clean, scripted video recordings  
**Duration**: ~20-30 seconds total with pauses  

### Option 2: Load Testing Demo
```bash
python load_test_100_users.py --mode sequential
```
**What**: 100 concurrent users triggering threats  
**Best for**: Showing system performance at scale  
**Duration**: ~2-3 minutes  

### Option 3: Interactive Demo
```bash
python demo_mode.py
```
**What**: Choose from credential stuffing, lateral movement, etc.  
**Best for**: Live presentations where you control the pace  
**Duration**: Variable (5-15 minutes)  

---

## 🧪 Running Tests

### Quick Test (Individual)
```bash
curl http://localhost:8000/health
```

### Full Test Suite (200 Tests)
```bash
python run_200_tests.py
```
**Expected result**: 95%+ tests pass  
**Duration**: 2-3 minutes  

### Load Test
```bash
python load_test_100_users.py --mode concurrent --workers 10
```
**Expected result**: See response times and throughput metrics  

### Postman Testing
1. Import `postman_collection.json` into Postman
2. Run the collection with pre-configured scenarios
3. See 4 threat level tests and validation checks

---

## 🔧 Configuration

### .env File (Optional)
```bash
# Database (CockroachDB) - optional, uses mock data if not set
CRDB_CONNECTION_STRING=postgresql://user:pass@host:26257/db

# AI Services - optional, uses fallback reasoning if not set
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
OPENAI_API_KEY=your_key

# Security Thresholds
SENTINEL_THREAT_THRESHOLD=5.0
```

**Note**: Demo works perfectly without any credentials configured!

---

## 📊 Dashboard Features

Once running at `http://localhost:3000`, you'll see:

- **Real-Time Threat Feed**: Live stream of detected threats
- **Threat Score**: 0-10 severity indicator (red = dangerous)
- **AI Reasoning**: Claude explains why it thinks something is suspicious
- **Event Timeline**: Historical context of all threats
- **Simulate Buttons**: Generate test events:
  - Suspicious (anonymous)
  - Suspicious (credential)
  - Suspicious (lateral movement)
  - Suspicious (multi-vector)

---

## 🎯 Common Commands

```bash
# Health check
curl http://localhost:8000/health

# Get recent events
curl http://localhost:8000/events

# Query threats (all endpoint at localhost:8000/events?threat_level=high)
curl "http://localhost:8000/events?threat_level=high"

# Interactive demo
python demo_mode.py

# Automated 5-event demo
python auto_demo.py

# Performance testing
python load_test_100_users.py --mode sequential

# Full test suite
python run_200_tests.py
```

---

## 🚀 Architecture Overview

```
┌─────────────────────────────────────────┐
│   React Dashboard (http://3000)         │
│   - Real-time threat display            │
│   - Simulate buttons                    │
│   - Performance metrics                 │
└──────────────┬──────────────────────────┘
               │
               │ API Calls
               ▼
┌─────────────────────────────────────────┐
│   Local Server (http://8000)            │
│   - REST API endpoints                  │
│   - CORS middleware                     │
│   - Request routing                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Sentinel Agent                        │
│   - Threat detection logic              │
│   - Event analysis                      │
│   - AI reasoning (Bedrock/OpenAI)       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Services                              │
│   - Embedding Service (vectors)         │
│   - Reasoning Agent (AI)                │
│   - Database Connection (CockroachDB)   │
└─────────────────────────────────────────┘
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | `lsof -i :8000` to find process, `kill -9 PID` to kill it |
| Frontend connection error | Check CORS - backend must be running first |
| No data in dashboard | Refresh browser, run `auto_demo.py` in another terminal |
| Slow performance | Close other apps, check Python process resources |
| Tests fail | Some may fail based on threshold config - 95%+ should pass |

---

## 📚 Learn More

- **`ARCHITECTURE.md`** - Deep technical explanation
- **`DEMO_VIDEO_GUIDE.md`** - Full video production strategy
- **`VIDEO_DEMO_READINESS.md`** - Pre-recording checklist
- **`CREDENTIALS_SETUP.md`** - External service configuration
- **`TEST_SUITE_README.md`** - Testing documentation

---

## ✨ Next Steps

1. ✅ Install dependencies
2. ✅ Start backend and frontend
3. ✅ Run `python auto_demo.py`
4. ✅ Watch dashboard update with threats
5. ✅ Record video or share live
6. 🎉 Done!

---

**Questions?** Check the relevant documentation file above or review the source code in `src/` directory.

**Ready to record?** Use the `VIDEO_DEMO_READINESS.md` checklist before recording.

---

**Sentinel: The threat detector that remembers everything.** 🛡️
