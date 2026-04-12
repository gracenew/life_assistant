import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.context_builder import build_data_summary
from app.database import get_db
from app import schemas
from app import ai_service

router = APIRouter(prefix="/api", tags=["chat"])

SYSTEM_PROMPT = """你是用户的本地生活助理，帮助管理日程、任务、财务、笔记与习惯。回答用中文，简洁、可执行。
用户数据摘要（可能为空）仅作参考，不要编造未在摘要中出现的事实；若用户要求写入数据，请说明可在左侧对应模块填写，或稍后由系统扩展自动写入。"""


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(body: schemas.ChatRequest, db: Session = Depends(get_db)):
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(400, "消息不能为空")

    summary = build_data_summary(db)
    user_content = f"【本地数据摘要】\n{summary}\n\n【用户问题】\n{msg}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        provider = ai_service.resolve_provider(body.provider)
        reply, provider, model = await ai_service.chat_completion(
            messages,
            provider=provider,
            model=body.model,
        )
    except (ValueError, RuntimeError) as e:
        provider = (body.provider or "").strip().lower() or "ollama"
        return schemas.ChatResponse(reply="", provider=provider, model=body.model or "", error=str(e))
    except httpx.RequestError as e:
        return schemas.ChatResponse(
            reply="",
            provider=provider,
            model=body.model or "",
            error=ai_service.provider_error_message(provider, e),
        )
    except Exception as e:  # noqa: BLE001
        return schemas.ChatResponse(
            reply="",
            provider=provider,
            model=body.model or "",
            error=ai_service.provider_error_message(provider, e),
        )

    if not reply:
        return schemas.ChatResponse(
            reply="",
            provider=provider,
            model=model,
            error="模型返回空内容。请检查当前 provider 配置、模型名称以及鉴权信息是否正确。",
        )

    return schemas.ChatResponse(reply=reply, provider=provider, model=model, error=None)
