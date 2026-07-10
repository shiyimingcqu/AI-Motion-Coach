import io
import json
import os
import secrets
import time
import urllib.parse
import urllib.request

try:
    from fastapi import APIRouter, Depends, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = None
    BaseModel = Field = None
    StreamingResponse = None

from app.db.session import SessionLocal
from app.models.entities import UserORM
from app.core.security import create_access_token, get_password_hash

import requests

router = APIRouter(tags=["wechat"]) if APIRouter else None
WX_API_BASE = "https://api.weixin.qq.com"

LOGIN_TICKETS: dict[str, dict] = {}


def _get_access_token() -> str:
    appid = os.getenv("WECHAT_APPID", "")
    secret = os.getenv("WECHAT_SECRET", "")
    if not appid or not secret:
        raise HTTPException(status_code=500, detail="微信小程序配置未设置")
    resp = requests.get(
        f"{WX_API_BASE}/cgi-bin/token",
        params={"grant_type": "client_credential", "appid": appid, "secret": secret},
        timeout=10,
    )
    data = resp.json()
    if "errcode" in data and data["errcode"] != 0:
        raise HTTPException(status_code=502, detail=f"获取 access_token 失败: {data.get('errmsg', '')}")
    return data["access_token"]


if router:

    @router.get("/wechat/web-login/ticket")
    def create_login_ticket():
        """第一步：创建登录 ticket，返回 ticket ID（短 token，适配微信 scene 32 字节限制）"""
        ticket = secrets.token_hex(6)  # 12 位 hex，scene: "web_login=xxx" 共 21 字节
        LOGIN_TICKETS[ticket] = {"status": "pending", "token": None, "created_at": time.time()}
        return {"ticket": ticket}

    @router.get("/wechat/web-login/qrcode/{ticket}")
    def get_login_qrcode(ticket: str):
        """第二步：根据 ticket 生成微信小程序码 PNG"""
        import logging
        logger = logging.getLogger("wechat")
        record = LOGIN_TICKETS.get(ticket)
        if not record:
            raise HTTPException(status_code=404, detail="ticket 不存在或已过期")

        try:
            token = _get_access_token()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"获取 access_token 失败: {str(e)}")

        scene = f"web_login={ticket}"
        body = {
            "scene": scene,
            "page": "pages/web-login/web-login",
            "check_path": False,
            "env_version": "develop",
            "width": 280,
        }
        logger.info("requesting wxacode with body: %s", body)

        try:
            resp = requests.post(
                f"{WX_API_BASE}/wxa/getwxacodeunlimit",
                params={"access_token": token},
                json=body,
                timeout=15,
            )
        except requests.RequestException as e:
            raise HTTPException(status_code=502, detail=f"调用微信接口失败: {str(e)}")

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"微信接口返回 {resp.status_code}")

        content_type = resp.headers.get("content-type", "")
        logger.info("wxacode response status=%s content-type=%s size=%s", resp.status_code, content_type, len(resp.content))
        if "application/json" in content_type or "text" in content_type:
            err_data = resp.json()
            raise HTTPException(
                status_code=502,
                detail=f"生成小程序码失败: {err_data.get('errmsg', '')} (errcode: {err_data.get('errcode', '')})",
            )

        return StreamingResponse(io.BytesIO(resp.content), media_type="image/png")

    @router.get("/wechat/web-login/status/{ticket}")
    def poll_login_status(ticket: str):
        """第三步：Web 端轮询登录状态"""
        record = LOGIN_TICKETS.get(ticket)
        if not record:
            return {"status": "expired"}
        if record["status"] == "done":
            token = record["token"]
            del LOGIN_TICKETS[ticket]
            return {"status": "done", "token": token}
        if time.time() - record["created_at"] > 300:
            del LOGIN_TICKETS[ticket]
            return {"status": "expired"}
        return {"status": "pending"}

    if BaseModel:
        class WebWechatLoginRequest(BaseModel):
            code: str = Field(..., min_length=1)
            ticket: str = Field(..., min_length=1)

    @router.post("/wechat/web-login/login")
    def web_wechat_login(request: WebWechatLoginRequest if WebWechatLoginRequest else None):
        """小程序端：code + ticket → 登录"""
        if request is None:
            raise HTTPException(status_code=500, detail="依赖不可用")

        record = LOGIN_TICKETS.get(request.ticket)
        if not record:
            raise HTTPException(status_code=404, detail="ticket 不存在或已过期")

        appid = os.getenv("WECHAT_APPID", "")
        secret = os.getenv("WECHAT_SECRET", "")
        if not appid or not secret:
            raise HTTPException(status_code=500, detail="微信配置未设置")

        try:
            wx_url = "https://api.weixin.qq.com/sns/jscode2session"
            wx_params = {
                "appid": appid,
                "secret": secret,
                "js_code": request.code,
                "grant_type": "authorization_code",
            }
            full_url = f"{wx_url}?{urllib.parse.urlencode(wx_params)}"
            with urllib.request.urlopen(full_url, timeout=10) as resp:
                wx_data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"微信服务调用失败: {str(exc)}")

        if "errcode" in wx_data and wx_data["errcode"] != 0:
            raise HTTPException(status_code=400, detail=f"微信登录失败: {wx_data.get('errmsg', '')}")

        openid = wx_data.get("openid")
        if not openid:
            raise HTTPException(status_code=400, detail="获取 openid 失败")

        db = SessionLocal()
        try:
            user = db.query(UserORM).filter(UserORM.openid == openid).first()
            if user is None:
                username = f"wx_{openid[:16]}"
                counter = 0
                while db.query(UserORM).filter(UserORM.username == username).first():
                    counter += 1
                    username = f"wx_{openid[:12]}{counter}"
                user = UserORM(
                    username=username,
                    hashed_password=get_password_hash(openid),
                    openid=openid,
                    role="user",
                    nickname=username,
                    occupation="健身爱好者",
                    height="0", weight="0",
                    training_preferences=json.dumps(["增肌塑形"], ensure_ascii=False),
                    avatar_mode="default",
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            if not user.is_active:
                raise HTTPException(status_code=403, detail="用户已被禁用")

            access_token = create_access_token(data={"sub": user.username, "role": user.role})
            record["status"] = "done"
            record["token"] = access_token
            return {"message": "登录成功"}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
