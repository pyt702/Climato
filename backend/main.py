from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.chat_controller import router
from contextlib import asynccontextmanager
from repositories.weather_repo import setup_indexes

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_indexes()
    yield

app = FastAPI(title="Climato API", lifespan=lifespan)

# Setup CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
