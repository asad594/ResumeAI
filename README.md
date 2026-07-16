# AI Resume Analyzer

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-24-2496ED?style=for-the-badge&logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/TypeScript-5.6-3178C6?style=for-the-badge&logo=typescript" alt="TypeScript">
</p>

A production-ready AI-powered resume analysis platform that helps job seekers optimize their resumes with ATS scoring, skill gap analysis, job matching, and professional suggestions.

![ResumeAI Dashboard](./screenshot.png)

## Features

- **Smart Resume Upload** - Drag & drop PDF/DOCX with progress tracking
- **ATS Score Analysis** - Detailed scoring across formatting, keywords, experience, education, and skills
- **Skill Gap Analysis** - Compare your resume against job descriptions
- **Job Matching** - AI-powered similarity scoring and role recommendations
- **Professional Suggestions** - Actionable insights for resume improvement
- **Analytics Dashboard** - Charts, trends, and activity tracking
- **JWT Authentication** - Secure login, register, and password management
- **History Management** - Track all past analyses with search and pagination
- **Dark/Light Mode** - Theme toggle with system preference
- **Responsive Design** - Works on desktop, tablet, and mobile
- **PDF Report Generation** - Download comprehensive analysis reports
- **Docker Deployment** - One-command deployment with Docker Compose

## Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI | REST API framework |
| SQLAlchemy | ORM & Database |
| PostgreSQL | Database |
| Alembic | Migrations |
| JWT | Authentication |
| OpenAI API | AI Analysis |
| Pydantic | Validation |

### Frontend
| Technology | Purpose |
|-----------|---------|
| Next.js 15 | React Framework |
| TypeScript | Type Safety |
| Tailwind CSS | Styling |
| shadcn/ui | UI Components |
| Framer Motion | Animations |
| Recharts | Charts |
| Lucide Icons | Icons |

## Architecture

```
AI-Resume-Analyzer/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Config, security, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   └── uploads/            # Resume storage
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/            # Pages & routes
│       ├── components/     # Reusable components
│       ├── context/        # React context
│       ├── hooks/          # Custom hooks
│       ├── lib/            # Utilities & API
│       └── types/          # TypeScript types
├── tests/                  # Test suites
├── docker/                 # Docker configs
├── scripts/                # Setup scripts
├── docs/                   # Documentation
└── docker-compose.yml      # Docker orchestration
```

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 16+
- Docker & Docker Compose (optional)

### Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-resume-analyzer.git
cd ai-resume-analyzer

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# Set OPENAI_API_KEY for AI features

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/api/v1/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database URL and API keys

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://postgres:postgres@localhost:5432/resume_analyzer |
| SECRET_KEY | JWT secret key | Change this! |
| ALGORITHM | JWT algorithm | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry | 7 |
| OPENAI_API_KEY | OpenAI API key | - |
| CORS_ORIGINS | Allowed origins | ["http://localhost:3000"] |
| MAX_FILE_SIZE_MB | Max upload size | 10 |

### Frontend (.env.local)

| Variable | Description | Default |
|----------|-------------|---------|
| NEXT_PUBLIC_API_URL | Backend API URL | http://localhost:8000/api/v1 |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Get current user |
| PUT | `/api/v1/auth/me` | Update profile |
| POST | `/api/v1/auth/change-password` | Change password |

### Resumes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resumes/upload` | Upload resume |
| GET | `/api/v1/resumes/` | List resumes |
| GET | `/api/v1/resumes/:id` | Get resume |
| DELETE | `/api/v1/resumes/:id` | Delete resume |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/analysis/` | Create analysis |
| GET | `/api/v1/analysis/` | Get history |
| GET | `/api/v1/analysis/analytics` | Get analytics |
| GET | `/api/v1/analysis/:id` | Get analysis |
| DELETE | `/api/v1/analysis/:id` | Delete analysis |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jobs/` | List saved jobs |
| POST | `/api/v1/jobs/save` | Save job |
| DELETE | `/api/v1/jobs/:id` | Delete saved job |

## Security Features

- Password hashing with bcrypt
- JWT access & refresh tokens
- Rate limiting on API endpoints
- Input validation with Pydantic
- CORS protection
- File type validation
- File size limits
- SQL injection prevention (SQLAlchemy ORM)

## Testing

```bash
# Backend tests
cd backend
pytest

# Run specific tests
pytest tests/test_auth.py -v
pytest tests/test_resumes.py -v
```

## Design System

Based on the UI/UX Pro Max skill recommendations:

- **Theme**: Dark Mode (OLED)
- **Primary**: #3B82F6
- **Accent**: #60A5FA
- **Background**: #0F172A
- **Cards**: #1E293B
- **Border Radius**: 16px
- **Font**: Plus Jakarta Sans
- **Animations**: Smooth transitions (150-300ms)

## Deployment

### Production with Docker

```bash
# Build and start
docker-compose -f docker-compose.yml up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Production Deployment

```bash
# Backend
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Frontend
cd frontend
npm run build
npm start
```

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with modern technologies for production use.
</p>
