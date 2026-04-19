# TaxAssist - AI-Powered ITR Filing Assistant

A full-stack application for automated Form 16 extraction, ITR mapping, and filing assistance using OCR, LLM, and RAG.

## Project Structure

```
TaxAssist/
├── backend/              # Python FastAPI backend
│   ├── fastapi/         # FastAPI application core
│   ├── ocr/             # OCR extraction module
│   ├── rag/             # RAG pipeline for ITR recommendations
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Backend environment variables
├── taxeaseui/           # Next.js frontend application
│   ├── src/             # React/TypeScript source
│   ├── package.json     # Node.js dependencies
│   └── .env.local       # Frontend environment variables
└── README.md            # This file
```

## Prerequisites

- **Python 3.14.3+** for backend
- **Node.js 18+** and npm for frontend
- **PostgreSQL 12+** for database
- **Tesseract OCR** for text extraction
- **Git** for version control

## Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv myenv

# Activate virtual environment
# Windows:
myenv\Scripts\activate
# macOS/Linux:
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env and set:
# - DATABASE_URL=postgresql://user:password@localhost:5432/taxassist
# - GROQ_API_KEY=your_groq_api_key
# - SECRET_KEY=your_secret_key
```

### Frontend Setup

```bash
cd taxeaseui

# Install dependencies
npm install

# Configure environment
# Edit .env.local and set:
# NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Running Locally

### Start Backend

```bash
cd backend
source myenv/bin/activate  # or myenv\Scripts\activate on Windows
python -m uvicorn fastapi.app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### Start Frontend

```bash
cd taxeaseui
npm run dev
```

Frontend will be available at: `http://localhost:3000`

## API Endpoints

### OCR & Mapping
- `POST /upload` - Upload Form 16 file for OCR extraction and ITR mapping
- `PUT /upload/save` - Save updated mapping values (in-memory, not persisted for privacy)

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Chat & Assistance
- `POST /chat` - Query ITR assistance chatbot (RAG-powered)

### Health
- `GET /health` - Backend health check

## Deployment

### Database Migration

Ensure PostgreSQL is running and the database exists. The application automatically creates tables on startup.

### Backend Deployment

1. Set environment variables:
   ```
   DATABASE_URL=postgresql://prod_user:password@prod_host:5432/taxassist
   GROQ_API_KEY=your_production_api_key
   SECRET_KEY=your_production_secret_key
   ```

2. Run with production ASGI server:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 fastapi.app:app
   ```

### Frontend Deployment

1. Build for production:
   ```bash
   npm run build
   ```

2. Deploy the `.next` directory and `public` folder to your hosting platform (Vercel, AWS, Azure, etc.)

### Docker Deployment (Optional)

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.14.3-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "fastapi.app:app"]
```

Create `taxeaseui/Dockerfile`:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY taxeaseui/package*.json ./
RUN npm ci
COPY taxeaseui .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Key Features

- **Form 16 Extraction**: Automated OCR to extract financial data
- **AI-Powered Mapping**: LLM-based field extraction and validation
- **ITR Recommendations**: RAG pipeline for personalized ITR filing guidance
- **Interactive Dashboard**: Review and edit extracted data before submission
- **User Authentication**: Secure login and user management
- **Privacy-First**: Edits and data remain in-memory; no server persistence for sensitive information

## Configuration

### Backend Environment (.env)

```
DATABASE_URL=postgresql://user:password@localhost:5432/taxassist
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_jwt_secret_key
DEBUG=False
```

### Frontend Environment (.env.local)

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

## Technologies

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **LangChain** - LLM orchestration
- **FAISS** - Vector search
- **PyTesseract** - OCR
- **Groq** - LLM API

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Lucide Icons** - UI icons

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m 'Add your feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Open a pull request

## Privacy & Security

- Sensitive financial data is processed in-memory only
- No long-term persistence of user tax information
- HTTPS recommended for production
- Database credentials should never be committed

## Support

For issues or questions, please open a GitHub issue or contact the development team.

## License

This project is licensed under the MIT License - see LICENSE file for details.
