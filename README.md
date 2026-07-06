# Climato - AI Weather Assistant

Climato is a smart, AI-powered weather assistant built with a modern web stack. It uses LangGraph and Gemini to parse natural language queries, checks a local MongoDB cache, and fetches missing historical or forecast weather data directly from the free Open-Meteo API.

## Architecture

This repository is split into two main directories:

- **`backend/`**: A FastAPI application powered by LangGraph, LangChain, and MongoDB. It handles intelligent intent parsing, batch API requests, database caching, and conversational AI generation.
- **`frontend/`**: The frontend user interface for interacting with the AI chat and dynamically rendering beautiful weather widgets.

## Features

- **Natural Language Parsing**: Ask complex, multi-part queries like *"differences in weather of sydney today and weather on 1999 dec 31"*.
- **LangGraph Orchestration**: Intelligent node-based workflow for planning tasks, checking cache, and batch API retrieval.
- **Database Caching**: Uses MongoDB to efficiently cache daily weather data, dramatically reducing external API calls.
- **TTL Memory**: Retains conversation history using MongoDB TTL indexes for temporary memory injection.
- **100% Free Weather Data**: Uses the open-source Open-Meteo API. No API keys or paid tiers required.

## Prerequisites

- Python 3.10+
- Node.js & npm (for frontend)
- MongoDB instance running locally (or via MongoDB Atlas)
- Google Gemini API Key (for LangGraph/LLM orchestration)

---

## Setup Instructions

### 1. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Create a virtual environment and install dependencies:
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory with your environment variables:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017/  # Replace if using MongoDB Atlas
```

Start the FastAPI development server:
```bash
uvicorn main:app --reload
```
The backend will now be available at `http://localhost:8000`.

### 2. Frontend Setup

Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install the NPM dependencies:
```bash
npm install
```

Start the frontend development server:
```bash
npm run dev
```
The application UI should now be accessible in your browser (usually at `http://localhost:5173` or `http://localhost:3000`).

---

## The LangGraph Flow

Watch the terminal running your backend server when making requests. You will see detailed logs showing the agent dynamically navigating its nodes:
1. **Planner Node:** Extracts weather tasks (forecast or historical) based on the query.
2. **Database Node:** Checks MongoDB for cached data.
3. **Weather API Node (Fallback):** Only triggers to fetch missing dates/cities from Open-Meteo.
4. **Response Node:** Synthesizes all gathered data into a natural language response.
