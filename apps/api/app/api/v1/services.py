from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def list_services() -> dict:
    return {"items": []}


@router.get("/{service_id}/questions")
async def list_service_questions(service_id: str) -> dict:
    return {"service_id": service_id, "items": []}
