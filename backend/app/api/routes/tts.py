"""TTS 语音合成路由

使用 edge-tts（微软 Edge 浏览器在线 TTS 引擎）将文字合成为 MP3 音频。
小程序端通过 GET /api/tts?text=xxx 获取音频流，用 wx.createInnerAudioContext 播放。
"""

import io
import hashlib
import os
import time

try:
    from fastapi import APIRouter, Query
    from fastapi.responses import StreamingResponse
except ModuleNotFoundError:
    APIRouter = None
    Query = None
    StreamingResponse = None

router = APIRouter(tags=["tts"]) if APIRouter else None

# 简易内存缓存：text_hash -> (mp3_bytes, timestamp)
# 缓存 5 分钟，避免相同文本重复合成
_CACHE: dict[str, tuple[bytes, float]] = {}
_CACHE_TTL = 300  # 5 分钟

# 默认中文语音
_DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


def _cache_key(text: str, voice: str) -> str:
    raw = f"{voice}:{text}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _get_from_cache(key: str):
    entry = _CACHE.get(key)
    if not entry:
        return None
    data, ts = entry
    if time.time() - ts > _CACHE_TTL:
        del _CACHE[key]
        return None
    return data


def _put_cache(key: str, data: bytes):
    # 限制缓存大小，超过 200 条时清理最旧的
    if len(_CACHE) > 200:
        oldest = min(_CACHE, key=lambda k: _CACHE[k][1])
        del _CACHE[oldest]
    _CACHE[key] = (data, time.time())


async def _synthesize(text: str, voice: str) -> bytes:
    """用 edge-tts 合成语音，返回 MP3 字节"""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    audio_buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
    return audio_buffer.getvalue()


if router:

    @router.get("/tts")
    async def text_to_speech(
        text: str = Query(..., description="要合成的文字", max_length=200),
        voice: str = Query(_DEFAULT_VOICE, description="语音角色"),
    ):
        """文字转语音接口

        返回 audio/mpeg 格式的 MP3 音频流。
        小程序端用 wx.createInnerAudioContext() 播放。
        """
        text = text.strip()
        if not text:
            return {"error": "text is required"}

        # 截取前 100 字，保证响应速度
        text = text[:100]
        voice = voice or _DEFAULT_VOICE

        # 查缓存
        key = _cache_key(text, voice)
        cached = _get_from_cache(key)
        if cached:
            return StreamingResponse(
                io.BytesIO(cached),
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=300",
                    "X-TTS-Cache": "hit",
                },
            )

        # 合成
        try:
            audio_data = await _synthesize(text, voice)
        except Exception as e:
            return {"error": f"synthesis failed: {str(e)}"}

        if not audio_data:
            return {"error": "synthesis produced no audio"}

        _put_cache(key, audio_data)

        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=300",
                "X-TTS-Cache": "miss",
            },
        )
