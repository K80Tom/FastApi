import asyncio
import json

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.dependencies import CurrentUser
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.user import User
from app.services.permission_service import require_project_role

router = APIRouter(tags=["realtime"])


@router.get("/events/stream")
async def stream_events(request: Request, current_user: CurrentUser, limit: int = Query(default=3, ge=1, le=100)):
    async def generate():
        for event_id in range(1, limit + 1):
            if await request.is_disconnected():
                break
            payload = {"event": "heartbeat", "user_id": current_user.id, "sequence": event_id}
            yield f"id: {event_id}\nevent: heartbeat\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@router.websocket("/ws/projects/{project_id}")
async def project_socket(websocket: WebSocket, project_id: int):
    await websocket.accept()
    try:
        try:
            async with asyncio.timeout(5):
                message = await websocket.receive_json()
        except TimeoutError:
            await websocket.close(code=1008, reason="Authentication timeout")
            return
        token = message.get("token") if message.get("type") == "authenticate" else None
        if not token:
            await websocket.close(code=1008, reason="Authentication required")
            return
        settings = websocket.app.state.settings
        try:
            payload = decode_access_token(token, settings)
            user_id = int(payload["sub"])
        except Exception:
            await websocket.close(code=1008, reason="Invalid token")
            return
        async with websocket.app.state.session_factory() as session:
            user = await session.get(User, user_id)
            if user is None or not user.is_active:
                await websocket.close(code=1008, reason="Inactive user")
                return
            try:
                await require_project_role(session, user, project_id, "viewer")
            except AppError:
                await websocket.close(code=1008, reason="Project access denied")
                return
        await websocket.send_json({"type": "ready", "project_id": project_id, "user_id": user_id})
        while True:
            incoming = await websocket.receive_json()
            if incoming.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "message": "Unsupported message type"})
    except WebSocketDisconnect:
        return
