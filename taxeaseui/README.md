# TaxEase – AI-powered ITR Guidance System

TaxEase is a production-ready modern SaaS application designed for seamless tax insights and Form 16 mapping. Modeled after sleek modern fintech and cybersecurity dashboards, it delivers a high-trust, fast, and secure user experience.

## Features

- **Fintech UI/UX**: White and green specific palette (`#22C55E` primary, `#F8FAFC` background).
- **Dashboard Overview**: Financial insights with real-time trend reporting and charts.
- **Upload Form 16**: Smart Drag-and-Drop system to extract PDFs/Images natively on-the-fly.
- **ITR Mapping**: Review expanded field mapping to verify tax outputs effortlessly.
- **AI Assistant**: A responsive context-aware chat interface to answer tax queries dynamically.
- **Mock APIs included**: Features `/api/upload`, `/api/extract`, `/api/itr-map` using Next App Router.

## Tech Stack

- **Frontend**: Next.js 15 (App Router), React 19, Tailwind CSS v4.
- **Backend**: Next.js Serverless Route Handlers (`src/app/api/...`), Node.js.
- **Database (Schema ready)**: Expected to run on PostgreSQL or MongoDB.
- **UI Components**: Recharts, Lucide Icons, Framer Motion (Optional), Classnames.

## Setup Instructions

1. **Install Dependencies**
   Navigate to the repository folder and install dependencies via NPM.
   ```bash
   npm install
   ```

2. **Run Development Server**
   ```bash
   npm run dev
   ```

3. **Open the Application**
   Visit `http://localhost:3000` to view the running app.

## Folder Structure

```
├── public/                 # Static assets
├── src/
│   ├── app/                # Next.js App Router
│   │   ├── api/            # Backend API routes
│   │   ├── assistant/      # AI Assistant page
│   │   ├── mapping/        # ITR mapping interface
│   │   ├── upload/         # Form 16 Upload handling
│   │   ├── globals.css     # Theme design tokens & global css
│   │   ├── layout.tsx      # Core application layout
│   │   └── page.tsx        # Top-level Dashboard
│   ├── components/         # Reusable React components
│   │   ├── Sidebar.tsx     # Navigation sidebar
│   │   └── TopBar.tsx      # Header & search
```

## Deployment

Deploy this project on Vercel simply by importing the repository:
```bash
npx vercel
```
