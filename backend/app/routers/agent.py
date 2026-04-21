import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import agent_service, schemas
from app.database import get_db
from app.tools.registry import TOOL_DEFINITIONS

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/tools", response_model=list[schemas.AgentToolDefinitionOut])
def list_tools():
    return [
        schemas.AgentToolDefinitionOut(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        )
        for tool in TOOL_DEFINITIONS.values()
    ]


@router.post("/run", response_model=schemas.AgentRunResponse)
async def run_agent(body: schemas.AgentRunRequest, db: Session = Depends(get_db)):
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(400, "消息不能为空")

    try:
        result, provider, model = await agent_service.run_agent(
            db=db,
            message=msg,
            provider=body.provider,
            model=body.model,
            max_steps=body.max_steps,
        )
        return schemas.AgentRunResponse(
            answer=result["answer"],
            reasoning=result["reasoning"],
            provider=provider,
            model=model,
            tool_calls=[schemas.AgentToolCallOut(**item) for item in result["tool_calls"]],
            pending_actions=[schemas.AgentPendingActionOut(**item) for item in result["pending_actions"]],
            error=None,
        )
    except (ValueError, RuntimeError) as e:
        provider = (body.provider or "").strip().lower() or "ollama"
        return schemas.AgentRunResponse(
            answer="",
            reasoning="",
            provider=provider,
            model=body.model or "",
            tool_calls=[],
            pending_actions=[],
            error=str(e),
        )
    except httpx.RequestError as e:
        provider = (body.provider or "").strip().lower() or "ollama"
        return schemas.AgentRunResponse(
            answer="",
            reasoning="",
            provider=provider,
            model=body.model or "",
            tool_calls=[],
            pending_actions=[],
            error=f"Agent 调用模型或工具失败：{e!s}",
        )
    except Exception as e:  # noqa: BLE001
        provider = (body.provider or "").strip().lower() or "ollama"
        return schemas.AgentRunResponse(
            answer="",
            reasoning="",
            provider=provider,
            model=body.model or "",
            tool_calls=[],
            pending_actions=[],
            error=str(e),
        )


@router.post("/confirm", response_model=schemas.AgentConfirmResponse)
def confirm_action(body: schemas.AgentConfirmRequest, db: Session = Depends(get_db)):
    try:
        result = agent_service.confirm_action(db, body.action_type, body.payload)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return schemas.AgentConfirmResponse(**result)
