from fastapi import APIRouter

from ulabel.api.routers import assignments, exports, images, labelers, projects, stats, tokens

api_router = APIRouter()

api_router.include_router(tokens.router, prefix="/token", tags=["SignIn"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(assignments.router, prefix="/projects", tags=["Assignments"])
api_router.include_router(images.router, prefix="/projects", tags=["Images"])
api_router.include_router(exports.router, prefix="/projects", tags=["Exports"])
api_router.include_router(stats.router, prefix="/projects", tags=["Stats"])
api_router.include_router(labelers.router, prefix="/labelers", tags=["Labelers"])