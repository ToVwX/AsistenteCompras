from fastapi import FastAPI, HTTPException

from app.agent import ShoppingAssistantAgent
from app.config import settings
from app.memory import ConversationMemory
from app.schemas import ChatRequest, ChatResponse, HealthResponse, ResetResponse


settings.validate()
memory = ConversationMemory(max_messages=settings.max_history_messages)
agent = ShoppingAssistantAgent(settings=settings, memory=memory)

app = FastAPI(
    title="Asistente inteligente de compras de perifericos",
    description="Entregable 1: agente conversacional de compras y microservicio FastAPI.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="Sistema_ayuda_compras",
        provider=settings.provider,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="El mensaje no puede estar vacio.")
    try:
        result = agent.chat(message=message, session_id=request.session_id)
        return ChatResponse(
            response=result.response,
            session_id=request.session_id,
            tools_used=result.tools_used,
            provider=settings.provider,
        )
    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="El agente no pudo procesar la solicitud.",
        ) from error


@app.delete("/sessions/{session_id}", response_model=ResetResponse)
def reset_session(session_id: str) -> ResetResponse:
    memory.clear(session_id)
    return ResetResponse(
        message="Memoria de conversacion eliminada.", session_id=session_id
    )
