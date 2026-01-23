# 🎯 AI English Speaking Assessment Platform

An AI-powered platform that conducts natural English conversation assessments and provides comprehensive feedback on speaking skills.

---

## 🌟 Features

- **Natural AI Conversation:** Engage in a realistic conversation with an AI agent
- **Comprehensive Scoring:** 7 evaluation categories with detailed feedback
- **Real-time Analysis:** Speech-to-text, pronunciation assessment, and vision metrics
- **Full Audio Recording:** Complete conversation storage for review
- **Professional Reports:** Detailed score breakdown with actionable recommendations
- **User Dashboard:** Track progress and view assessment history

---

## 🏗️ Architecture

### Frontend
- **React** (Vite) + **Tailwind CSS**
- **Supabase Auth** for authentication
- **MediaPipe** for vision analysis
- **Web Audio API** for recording

### Backend
- **FastAPI** (Python)
- **Azure OpenAI** (GPT-4o)
- **Azure Speech Services** (STT/TTS)
- **Azure Blob Storage**

### Database
- **Supabase PostgreSQL**

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] **Node.js** 18+ installed
- [ ] **Python** 3.11+ installed
- [ ] **Azure Account** with:
  - Azure OpenAI access (requires approval)
  - Azure Speech Services
  - Azure Blob Storage
- [ ] **Supabase Account** (free tier available)
- [ ] **Git** installed

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd "d:/AI Projects/Soft Skill Check"
```

### 2. Configure Environment Variables

**Read the configuration guide:**
```bash
# Open and read ENV_TEMPLATE.md for detailed instructions
```

**Create your environment files:**

```bash
# Backend
cp .env.backend.template backend/.env.backend
# Then fill in your credentials

# Frontend
cp .env.frontend.template frontend/.env.frontend
# Then fill in your credentials
```

📖 **See `ENV_TEMPLATE.md` for detailed instructions on getting each credential**

### 3. Database Setup

```bash
# Follow Phase 1 in IMPLEMENTATION_PLAN.md
# Run SQL migrations in your Supabase project
```

### 4. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```
d:/AI Projects/Soft Skill Check/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Azure & Supabase integrations
│   │   ├── models/            # Data models
│   │   └── utils/             # Helper functions
│   ├── requirements.txt
│   └── .env.backend
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API clients
│   │   └── contexts/          # React contexts
│   ├── package.json
│   └── .env.frontend
│
├── database/                   # SQL migrations
│   └── migrations/
│
├── IMPLEMENTATION_PLAN.md      # Detailed step-by-step plan
├── ENV_TEMPLATE.md             # Environment setup guide
└── README.md                   # This file
```

---

## 📖 Documentation

- **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Complete 7-phase implementation guide
- **[ENV_TEMPLATE.md](./ENV_TEMPLATE.md)** - Environment variables setup guide
- **[Database Schema](./database/)** - Database migrations and structure

---

## 🎯 Assessment Flow

1. **Warm Welcome** - Introduction and instructions
2. **Normal Introduction** - Basic conversation
3. **Reading Assessment** - Read-aloud evaluation
4. **Listening Assessment** - Listen and repeat
5. **Storytelling** - Narrate a personal experience
6. **Opinion Question** - Discuss technology/AI
7. **Future Goals** - Share aspirations
8. **Results** - Comprehensive score report

---

## 📊 Scoring Categories

| Category | Max Score | Description |
|----------|-----------|-------------|
| Fluency | 20 | Speaking pace and flow |
| Pronunciation | 10 | Clarity and accuracy |
| Grammar | 10 | Sentence structure |
| Confidence | 20 | Voice steadiness |
| Hesitation | -10 | Penalty for fillers/pauses |
| Storytelling | 20 | Narrative quality |
| Vision Clarity | 10 | Eye contact & presence |
| **Total** | **100** | |

---

## 🛠️ Development Workflow

### Phase 0: Setup (Week 1)
- Environment configuration
- Azure & Supabase setup

### Phase 1: Database (Week 1-2)
- Schema creation
- RLS policies

### Phase 2: Backend (Week 2-4)
- API development
- Azure integrations
- Scoring engine

### Phase 3: Frontend (Week 4-7)
- UI components
- Audio/video capture
- API integration

### Phase 4: Integration (Week 7-8)
- End-to-end testing
- Bug fixes

### Phase 5: Deployment (Week 8-9)
- Azure deployment
- CI/CD setup

### Phase 6: Testing (Week 9-10)
- User testing
- Optimization

### Phase 7: Launch (Week 10-12)
- Documentation
- Soft launch

---

## 💰 Estimated Costs

**Monthly operational cost:** $50-150 for 50-100 users/day

**Breakdown:**
- Azure OpenAI: $30-80
- Azure Speech: $10-30
- Azure Blob Storage: $5-15
- Supabase: $0 (free tier) or $25 (pro)
- Azure App Service: $0-20

---

## 🔒 Security

- Row-level security (RLS) in Supabase
- Private blob storage with SAS URLs
- JWT authentication
- Rate limiting
- Input validation
- CORS configuration

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test

# E2E tests
npm run test:e2e
```

---

## 📦 Deployment

### Backend (Azure App Service)
```bash
cd backend
az webapp up --name your-app-name --resource-group your-rg
```

### Frontend (Azure Static Web Apps)
```bash
cd frontend
npm run build
# Deploy via GitHub Actions or Azure CLI
```

---

## 🤝 Contributing

1. Follow the implementation plan
2. Write tests for new features
3. Update documentation
4. Create pull requests

---

## 📄 License

[Your License Here]

---

## 🆘 Support

- **Documentation:** See `IMPLEMENTATION_PLAN.md` and `ENV_TEMPLATE.md`
- **Issues:** [GitHub Issues]
- **Email:** [Your Email]

---

## 🎉 Getting Started Now!

1. ✅ Read `IMPLEMENTATION_PLAN.md`
2. ✅ Follow `ENV_TEMPLATE.md` to get your credentials
3. ✅ Fill in `.env.backend` and `.env.frontend`
4. ✅ Start with Phase 0 of the implementation plan

**Let's build something amazing! 🚀**
