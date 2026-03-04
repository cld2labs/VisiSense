from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import catalog, chat


app = FastAPI(
    title=settings.SERVICE_NAME,
    description="Visual Product Intelligence for Retail Merchandising",
    version=settings.SERVICE_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(catalog.router, prefix="/api/v1", tags=["catalog"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "organization": "Cloud2 Labs",
        "llm_provider": settings.LLM_PROVIDER,
        "vision_model": settings.LLM_MODEL
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
