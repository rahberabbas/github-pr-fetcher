from fastapi import FastAPI, Request
from app.routes.tasks import router as task_router
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="GitHub PR Fetcher",
    description="API to fetch details of a GitHub Pull Request asynchronously using Celery and Redis.",
    version="1.0.0",
)


origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the routes
app.include_router(task_router)

