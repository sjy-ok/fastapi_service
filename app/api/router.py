from fastapi import APIRouter

from app.modules.health.router import router as health_router
from app.modules.personnels.router import router as personnels_router

router = APIRouter()
router.include_router(health_router)
router.include_router(personnels_router)
