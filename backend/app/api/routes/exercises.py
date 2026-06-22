from app.services.exercise.registry import list_exercises

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None

router = APIRouter(tags=["exercises"]) if APIRouter else None


if router:
    @router.get("/exercises")
    def get_exercises():
        return {"items": [exercise.to_dict() for exercise in list_exercises()]}
