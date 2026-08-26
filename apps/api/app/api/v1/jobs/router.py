from fastapi import APIRouter

from app.api.v1.jobs.read import router as read_router
from app.api.v1.jobs.transitions import router as transitions_router
from app.api.v1.jobs.work_requests import router as work_requests_router

router = APIRouter()
router.include_router(read_router)
router.include_router(transitions_router)
router.include_router(work_requests_router)
