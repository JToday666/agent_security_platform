"""Agent registration and management routes."""

from fastapi import APIRouter, Depends

from app.modules.agents.dependencies import get_agent_service
from app.modules.agents.schemas import (
    AgentArchiveResponse,
    AgentCreateRequest,
    AgentDetail,
    AgentSummary,
    AgentTemplate,
    AgentVerificationRequest,
    AgentVerificationResponse,
)
from app.modules.agents.service import AgentService
from app.modules.auth.dependencies import get_current_user
from app.platform.http import success_payload
from app.platform.schemas import Envelope

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/templates", response_model=Envelope[list[AgentTemplate]])
async def list_agent_templates(service: AgentService = Depends(get_agent_service)):
    """Return built-in Agent registration templates."""
    templates = await service.list_templates()
    return success_payload([template.model_dump(by_alias=True) for template in templates])


@router.post("", response_model=Envelope[AgentSummary])
async def create_agent(
    payload: AgentCreateRequest,
    current_user=Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Create a draft Agent."""
    response = await service.create_agent(payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.get("", response_model=Envelope[list[AgentSummary]])
async def list_agents(
    includeArchived: bool = False,
    status: str | None = None,
    current_user=Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """List current user's Agents."""
    response = await service.list_agents(current_user, include_archived=includeArchived, status=status)
    return success_payload([item.model_dump(by_alias=True) for item in response])


@router.get("/{agentId}", response_model=Envelope[AgentDetail])
async def get_agent_detail(
    agentId: str,
    current_user=Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Return non-sensitive Agent detail."""
    response = await service.get_agent_detail(agentId, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/{agentId}/verify", response_model=Envelope[AgentVerificationResponse])
async def verify_agent(
    agentId: str,
    payload: AgentVerificationRequest,
    current_user=Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Run live Agent verification."""
    response = await service.verify_agent(agentId, payload, current_user)
    return success_payload(response.model_dump(by_alias=True))


@router.post("/{agentId}/archive", response_model=Envelope[AgentArchiveResponse])
async def archive_agent(
    agentId: str,
    current_user=Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
):
    """Archive an Agent."""
    response = await service.archive_agent(agentId, current_user)
    return success_payload(response.model_dump(by_alias=True))
