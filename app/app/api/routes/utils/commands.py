from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import ExternalApiServiceDep, get_current_active_superuser
from app.models import ExternalTodoPublic, Message
from app.services.email_events import publish_test_email_event

router = APIRouter()


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """Test emails."""
    publish_test_email_event(email_to=str(email_to))
    return Message(message="Test email queued")


@router.post(
    "/external/warmup/",
    response_model=ExternalTodoPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
async def warmup_external_cache(service: ExternalApiServiceDep) -> ExternalTodoPublic:
    return await service.warmup_default_todo()
