"""Grounded RAG Agent Chat conversational endpoint."""

from fastapi import APIRouter, Depends, status

from app.core.auth import TenantContext, get_tenant_context
from app.llm.agent_service import rag_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Grounded RAG Agent Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Grounded RAG Agent using Qwen LLM",
)
async def chat_with_agent(
    payload: ChatRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ChatResponse:
    """Execute grounded question answering against user's documents.

    Guaranteed zero-hallucination: only answers from retrieved context chunks.
    If the question cannot be answered from the knowledge base, states it clearly.
    """
    return await rag_agent.chat(payload, tenant)


@router.get(
    "/suggestions",
    response_model=list[str],
    summary="Get dynamic suggested questions from real knowledge base",
)
async def get_chat_suggestions(
    tenant: TenantContext = Depends(get_tenant_context),
) -> list[str]:
    """Retrieve dynamic query suggestions based on indexed document chunks."""
    return await rag_agent.get_suggested_prompts(tenant)

