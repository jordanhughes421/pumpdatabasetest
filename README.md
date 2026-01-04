# Pump Curve Manager

A production-quality, web-based application for managing and visualizing centrifugal pump performance curves.

## Features

- **Pump Library**: Store manufacturer, model, and metadata.
- **Curve Management**: Organize curves into sets (e.g., specific RPM or Impeller).
- **Data Entry**: Paste data directly from Excel/CSV (Flow, Value).
- **Visualization**: Interactive plots for Head, Efficiency, and Power vs Flow.
- **Comparison**: Overlay multiple curves to compare performance.
- **Responsive UI**: Built with React and Tailwind CSS.

## Tech Stack

- **Backend**: Python, FastAPI, SQLModel (SQLAlchemy + Pydantic), SQLite.
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, TanStack Query, Plotly.js.
- **Deployment**: Docker, Docker Compose, Nginx.

## Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python seed.py  # (Optional) Seed with sample data
uvicorn backend.main:app --reload
```
Backend runs at `http://localhost:8000`. API Docs at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

## Deployment with Docker

The easiest way to run the full stack is with Docker Compose.

```bash
docker-compose up --build
```

- Access the App: `http://localhost:3000`
- Access the API: `http://localhost:8000`

## Configuration

- **Database**: Defaults to `database.db` (SQLite). Can be swapped for PostgreSQL by changing the `DATABASE_URL` in `backend/database.py`.
- **Environment**:
    - Frontend API URL is hardcoded to `http://localhost:8000` for simplicity in `frontend/src/api/client.ts`. For production, update this or use the Nginx proxy setup provided in Docker.

## Project Structure

- `backend/`: FastAPI application.
- `frontend/`: React Vite application.
- `docker-compose.yml`: Orchestration.

## Usage Guide

1. **Create a Pump**: Go to "Add New Pump", enter details.
2. **Add Curves**: Go to Pump Details -> "Add Curve Set".
3. **Enter Data**: Click the curve set name. Select "Head vs Flow". Paste data (e.g. "0 100\n100 90"). Click Save. Repeat for Efficiency/Power.
4. **Compare**: Click "Compare" in the nav bar. Select pumps and curve sets to overlay.
