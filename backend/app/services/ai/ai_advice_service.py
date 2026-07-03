import json
import os
import time
from pathlib import Path
import urllib.error
import urllib.request

from app.services.analysis.unified_feedback_service import UnifiedFeedbackResult


def generate_ai_advice(payload: dict) -> dict:
    """基于统一反馈结果做语言包装，不做独立判断。

    Args:
        payload: 包含统一反馈格式化的数据，由 ExerciseAnalyzer.get_ai_advice_payload() 生成
    """
    env_overrides = _load_env_example()
    api_url = os.getenv("AI_API_URL", "").strip() or env_overrides.get("AI_API_URL", "")
    api_key = os.getenv("AI_API_KEY", "").strip() or env_overrides.get("AI_API_KEY", "")
    model = os.getenv("AI_MODEL", "").strip() or env_overrides.get("AI_MODEL", "ernie-4.5-turbo-32k")
    timeout_raw = os.getenv("AI_API_TIMEOUT", "").strip() or env_overrides.get("AI_API_TIMEOUT", "60")
    timeout = int(timeout_raw)
    if "/chat/completions" not in api_url:
        if api_url.endswith("/v2"):
            api_url = f"{api_url}/chat/completions"
        elif api_url.endswith("/v2/"):
            api_url = f"{api_url}chat/completions"
        else:
            api_url = api_url.rstrip("/") + "/v2/chat/completions"

    if not api_url or not api_key:
        raise ValueError("AI advice failed: missing AI_API_URL or AI_API_KEY")

    prompt = build_prompt_from_unified_feedback(payload)
    print(f"AI advice request: model={model} url={api_url} timeout={timeout}s unified_feedback=enabled")
    started_at = time.monotonic()
    request_body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一位亲切、专业的健身动作教练，擅长把系统检测到的动作问题转化为温暖、易懂、有行动力的训练建议。\n"
                    "写作要求：\n"
                    "1. 仅基于用户提供的「检测到的问题」和「系统建议」作答，不编造未提及的问题。\n"
                    "2. 语气积极鼓励，措辞自然流畅，避免生硬说教或机械罗列。\n"
                    "3. 使用 Markdown 排版，四个固定小节标题分别为：\n"
                    "   ## 🌟 整体评价\n"
                    "   ## ⚠️ 主要问题\n"
                    "   ## 💡 改进建议\n"
                    "   ## 🎯 下次训练重点\n"
                    "4. 每个小节标题保留 emoji；正文可适度使用 emoji 点缀（每节 1-3 个），但不要堆砌。\n"
                    "5. 「改进建议」用有序列表（1. 2. 3.），每条建议具体可执行，聚焦动作细节（姿态、深度、节奏、发力等）。\n"
                    "6. 「下次训练重点」控制在 1-2 句话，简洁有力。\n"
                    "7. 禁止提及完成次数、有效次数、计数、评分、百分比等任何统计数据；"
                    "只谈动作质量本身及如何改进。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 800,
    }

    request = urllib.request.Request(
        api_url,
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", "ignore").strip()
        print(f"AI advice HTTPError: status={exc.code}, reason={exc.reason}, body={error_body}")
        detail = error_body[:300] if error_body else exc.reason
        raise ValueError(f"AI advice failed: provider returned {exc.code}, detail={detail}") from exc
    except urllib.error.URLError as exc:
        print(f"AI advice URLError: reason={exc.reason}")
        raise ValueError(f"AI advice failed: network error, detail={exc.reason}") from exc
    text = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not text:
        raise ValueError("AI advice failed: empty response content")
    elapsed = time.monotonic() - started_at
    print(f"AI advice success: {elapsed:.1f}s, {len(text)} chars")
    return {"text": text, "source": "llm"}


def build_prompt_from_unified_feedback(payload: dict) -> str:
    """从统一反馈格式构建 prompt，仅传递动作问题与建议，不含次数/评分。"""
    exercise = payload.get("exercise", "squat")
    errors = payload.get("errors", [])
    feedbacks = payload.get("feedbacks", [])

    exercise_label = {
        "squat": "深蹲",
        "push_up": "俯卧撑",
        "plank": "平板支撑",
        "jumping_jack": "开合跳",
    }.get(exercise, exercise)

    sections = [f"【动作类型】{exercise_label}"]

    if errors:
        sections.append(f"【检测到的问题】{'; '.join(errors)}")
    else:
        sections.append("【检测到的问题】无明显问题")

    if feedbacks:
        sections.append(f"【系统建议】{'; '.join(feedbacks)}")

    sections.append(
        "\n请基于以上动作问题与建议，用 Markdown 输出一份美观、温暖、可执行的动作指导报告。"
        "只讨论动作形态与改进方法，不要提及次数、有效次数、评分或任何统计数据。"
        "严格按以下四个小节输出，标题必须完全一致："
    )
    sections.append("## 🌟 整体评价")
    sections.append("（2-3 句话，肯定训练态度或做得好的方面，语气真诚）")
    sections.append("## ⚠️ 主要问题")
    sections.append("（解释检测到的动作问题及可能原因，通俗易懂，不夸大）")
    sections.append("## 💡 改进建议")
    sections.append("（用有序列表给出 3-4 条具体、可落地的动作改进方法）")
    sections.append("## 🎯 下次训练重点")
    sections.append("（1-2 句话，说明下次最应优先改善的动作细节）")

    return "\n".join(sections)


def _load_env_example() -> dict:
    root = Path(__file__).resolve().parents[4]
    env_file = root / ".env.example"
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value:
            values[key] = value
    if values:
        print("AI advice loaded config from .env.example")
    return values
