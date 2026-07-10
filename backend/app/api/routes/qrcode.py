import io
import os
from typing import Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from fastapi.responses import StreamingResponse
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = Query = None
    StreamingResponse = None

from app.api.deps import get_current_active_user
from app.core.config import settings
import requests

router = APIRouter(tags=["qrcode"]) if APIRouter else None

WX_API_BASE = "https://api.weixin.qq.com"


def _get_access_token() -> str:
    """获取微信小程序 access_token"""
    appid = os.getenv("WECHAT_APPID", "")
    secret = os.getenv("WECHAT_SECRET", "")
    if not appid or not secret:
        raise HTTPException(status_code=500, detail="微信小程序配置未设置（WECHAT_APPID / WECHAT_SECRET）")

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

    @router.get("/qrcode")
    def generate_wxacode(
        exercise: str = Query(..., description="动作类型，如 squat"),
        view: str = Query("side", description="拍摄视角"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """
        生成微信小程序码（小程序B路径：
        扫码 → pages/training/training?exercise=xxx&view=xxx）
        返回 PNG 图片
        """
        try:
            token = _get_access_token()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"获取 access_token 失败: {str(e)}")

        scene = f"exercise={exercise}&view={view}"
        body = {
            "scene": scene,
            "page": "pages/training/training",
            "check_path": False,
            "env_version": "trial",  # develop / trial / release
            "width": 280,
        }

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
        # 微信返回 image/jpeg 表示成功，返回 application/json 表示错误
        if "application/json" in content_type or "text" in content_type:
            err_data = resp.json()
            raise HTTPException(
                status_code=502,
                detail=f"生成小程序码失败: {err_data.get('errmsg', '')} (errcode: {err_data.get('errcode', '')})",
            )

        return StreamingResponse(io.BytesIO(resp.content), media_type="image/png")

    @router.get("/qrcode/env")
    def set_qrcode_env(
        env: str = Query("trial", description="develop / trial / release"),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """
        切换小程序码的目标环境（开发版 / 体验版 / 正式版）
        """
        if env not in ("develop", "trial", "release"):
            raise HTTPException(status_code=400, detail="env 必须是 develop / trial / release")
        return {"env": env}
