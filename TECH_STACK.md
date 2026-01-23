# 🛠️ TECHNOLOGY STACK OVERVIEW

Complete overview of all technologies, tools, and services used in this project.

---

## 🎨 FRONTEND STACK

### Core Framework
- **React 18+** - UI library
  - Why: Component-based, large ecosystem, excellent for SPAs
  - Installation: Via Vite template
  
- **Vite** - Build tool
  - Why: Lightning-fast HMR, optimized builds, better DX than CRA
  - Installation: `npm create vite@latest`

### Styling
- **Tailwind CSS** - Utility-first CSS framework
  - Why: Rapid development, consistent design, small production bundle
  - Installation: `npm install -D tailwindcss postcss autoprefixer`

### Routing
- **React Router v6** - Client-side routing
  - Why: Standard for React SPAs, declarative routing
  - Installation: `npm install react-router-dom`

### State Management
- **React Context API** - Global state
  - Why: Built-in, sufficient for this app size
  - For larger apps: Consider Zustand or Redux Toolkit

### Authentication
- **Supabase Auth** - Authentication provider
  - Why: Built-in auth, RLS integration, email/social login
  - Installation: `npm install @supabase/supabase-js`

### Media Processing
- **MediaPipe** - Vision & face detection
  - Why: Free, client-side processing, accurate face landmarks
  - Installation: `npm install @mediapipe/tasks-vision`
  
- **Web Audio API** - Audio recording
  - Why: Native browser API, real-time processing
  - No installation needed (browser native)

### HTTP Client
- **Axios** - HTTP requests
  - Why: Interceptors, better error handling than fetch
  - Installation: `npm install axios`
  - Alternative: Native `fetch` API

### UI Components (Optional)
- **Radix UI** or **Headless UI** - Accessible primitives
  - Why: Unstyled, accessible, works with Tailwind
  - Installation: `npm install @radix-ui/react-*`

### Data Visualization
- **Chart.js** or **Recharts** - Charts for results
  - Why: Simple, responsive charts for score display
  - Installation: `npm install react-chartjs-2 chart.js`

### Animations
- **Framer Motion** - React animations
  - Why: Declarative animations, smooth transitions
  - Installation: `npm install framer-motion`

---

## ⚙️ BACKEND STACK

### Core Framework
- **FastAPI** - Python web framework
  - Why: Fast, async, automatic API docs, type hints
  - Installation: `pip install fastapi`
  
- **Uvicorn** - ASGI server
  - Why: Production-grade async server
  - Installation: `pip install uvicorn[standard]`

### Database Client
- **Supabase Python Client** - Database & Auth
  - Why: Native Supabase integration, RLS support
  - Installation: `pip install supabase`
  
- **psycopg2** or **asyncpg** - PostgreSQL driver (if needed)
  - Installation: `pip install psycopg2-binary`

### Azure SDK
- **Azure OpenAI SDK**
  - Why: Official SDK, handles auth & retries
  - Installation: `pip install openai`
  
- **Azure Speech SDK**
  - Why: Real-time STT/TTS, pronunciation assessment
  - Installation: `pip install azure-cognitiveservices-speech`
  
- **Azure Blob Storage SDK**
  - Why: Efficient file uploads, SAS URL generation
  - Installation: `pip install azure-storage-blob`

### Audio Processing
- **librosa** - Audio analysis
  - Why: Extract pitch, volume, silence, pace
  - Installation: `pip install librosa`
  
- **pydub** - Audio conversions
  - Why: Format conversion, audio manipulation
  - Installation: `pip install pydub`
  - Also requires: `ffmpeg` (system dependency)

### Data Validation
- **Pydantic** - Data validation
  - Why: Built into FastAPI, type safety
  - Installed with FastAPI

### Environment Variables
- **python-dotenv** - Load .env files
  - Installation: `pip install python-dotenv`

### Security
- **python-jose** - JWT tokens
  - Installation: `pip install python-jose[cryptography]`
  
- **passlib** - Password hashing
  - Installation: `pip install passlib[bcrypt]`

### Testing
- **pytest** - Testing framework
  - Installation: `pip install pytest pytest-asyncio`
  
- **httpx** - Async HTTP client for testing
  - Installation: `pip install httpx`

---

## 🗄️ DATABASE & STORAGE

### Primary Database
- **Supabase PostgreSQL** - Relational database
  - Why: Managed PostgreSQL, built-in auth, RLS, real-time
  - Free tier: 500MB database
  - Setup: Create project at supabase.com

### File Storage
- **Azure Blob Storage** - Object storage
  - Why: Cheap, scalable, Azure ecosystem integration
  - Cost: ~$0.02/GB per month
  - Setup: Create storage account in Azure Portal

### Caching (Optional - Phase 2)
- **Redis** - In-memory cache
  - Why: Fast API response caching, session storage
  - Installation: Azure Cache for Redis or self-hosted
  - For now: Skip unless needed

---

## 🤖 AI & MACHINE LEARNING

### Language Model
- **Azure OpenAI - GPT-4o** - Conversation & scoring
  - Why: Most capable model, structured outputs, Azure integration
  - Cost: ~$0.005 per 1K input tokens, ~$0.015 per 1K output tokens
  - Requires: Azure OpenAI access approval

### Speech Services
- **Azure Speech Service** - STT & TTS
  - Features:
    - Speech-to-Text (real-time)
    - Text-to-Speech (neural voices)
    - Pronunciation Assessment
  - Cost: Free tier 5 hours/month, then ~$1/hour
  - Requires: Azure account

### Computer Vision
- **MediaPipe Face Detection** - Client-side vision
  - Why: Free, no API costs, privacy-friendly (no video upload)
  - Runs in browser
  - No backend needed

---

## ☁️ CLOUD & DEPLOYMENT

### Hosting
- **Azure Static Web Apps** - Frontend hosting
  - Why: Free tier, CDN, auto HTTPS, CI/CD
  - Cost: Free tier available
  
- **Azure App Service** - Backend hosting
  - Why: Managed Python hosting, scaling, monitoring
  - Cost: ~$13/month (Basic tier) or Free tier for development

### CI/CD
- **GitHub Actions** - Automated deployment
  - Why: Free for public repos, Azure integration
  - Setup: Auto-configured with Azure Static Web Apps

### Monitoring
- **Azure Application Insights** - Performance monitoring
  - Why: Integrated with Azure, auto-instrumentation
  - Cost: Pay-as-you-go
  
- **Sentry** (Optional) - Error tracking
  - Why: Better error UX, source maps
  - Free tier: 5K errors/month

### Domain & SSL
- **Azure DNS** or **Cloudflare** - Domain management
  - Why: Global CDN, DDoS protection
  - Cost: ~$10/year for domain

---

## 🔧 DEVELOPMENT TOOLS

### Version Control
- **Git** - Source control
- **GitHub** - Repository hosting

### Code Editors
- **VS Code** - Recommended IDE
  - Extensions:
    - Python
    - ESLint
    - Prettier
    - Tailwind CSS IntelliSense
    - Azure Tools

### API Testing
- **Postman** or **Insomnia** - API testing
- **Thunder Client** - VS Code extension

### Database Tools
- **Supabase Dashboard** - Built-in SQL editor
- **DBeaver** (Optional) - Database client

---

## 📦 PACKAGE MANAGERS

### Frontend
- **npm** - Default Node package manager
- **pnpm** (Alternative) - Faster, disk-efficient
- **yarn** (Alternative) - Facebook's package manager

### Backend
- **pip** - Python package manager
- **poetry** (Alternative) - Better dependency management

---

## 🔒 SECURITY & COMPLIANCE

### Authentication
- **Supabase Auth** - Session management
- **JWT** - Token-based auth for API

### Data Protection
- **Row Level Security (RLS)** - Database-level security
- **HTTPS** - Encrypted connections
- **SAS URLs** - Time-limited blob access

### Privacy
- **No video storage** - Only metrics extracted
- **Audio retention policy** - Auto-delete after 30-90 days
- **GDPR compliance** - User data deletion

---

## 💰 COST BREAKDOWN (Monthly)

### Free Tier Usage (~0-50 users/day)
- Supabase: **$0** (Free tier)
- Azure OpenAI: **$10-30** (pay-per-use)
- Azure Speech: **$5-15**
- Azure Blob: **$1-3**
- Azure Static Web Apps: **$0** (Free tier)
- Azure App Service: **$0** (Free tier)
- **Total: $16-48/month**

### Paid Tier (~100-500 users/day)
- Supabase: **$25** (Pro tier)
- Azure OpenAI: **$50-100**
- Azure Speech: **$20-40**
- Azure Blob: **$5-10**
- Azure Static Web Apps: **$0**
- Azure App Service: **$13** (Basic B1)
- **Total: $113-188/month**

### Enterprise (~1000+ users/day)
- Scale up Azure services
- Add Redis caching
- Load balancing
- **Estimated: $500-1000/month**

---

## 🔄 ALTERNATIVES CONSIDERED

### OpenAI API vs Azure OpenAI
✅ **Chose Azure OpenAI:**
- Better enterprise support
- Data privacy (doesn't train on your data)
- Integrated with other Azure services
- Regional deployment

❌ **OpenAI API:**
- Simpler setup
- Faster access (no approval needed)
- Better for prototyping

### Google Cloud Speech vs Azure Speech
✅ **Chose Azure Speech:**
- Better pronunciation assessment
- Neural TTS voices
- All services in one cloud

### Firebase vs Supabase
✅ **Chose Supabase:**
- PostgreSQL (relational)
- Row-level security
- Open source
- Better for complex queries

---

## 📚 DOCUMENTATION LINKS

**Frontend:**
- [React Docs](https://react.dev)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [MediaPipe](https://developers.google.com/mediapipe)

**Backend:**
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure Speech](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/)
- [Supabase Docs](https://supabase.com/docs)

**Deployment:**
- [Azure Static Web Apps](https://learn.microsoft.com/en-us/azure/static-web-apps/)
- [Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/)

---

## ✅ FINAL RECOMMENDATIONS

### For Development
1. Start with free tiers of all services
2. Use VS Code with recommended extensions
3. Test locally before deploying
4. Use Postman for API testing

### For Production
1. Upgrade to paid tiers based on usage
2. Set up monitoring (Application Insights)
3. Configure CI/CD pipelines
4. Implement proper error handling
5. Add rate limiting
6. Regular security audits

---

**Next:** Review `CREDENTIALS_GUIDE.md` to get your API keys! 🚀
