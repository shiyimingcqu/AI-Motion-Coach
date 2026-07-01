import json
import os
import time
from pathlib import Path
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
    model = os.getenv("AI_MODEL", "").strip() or env_overrides.get("AI_MODEL", "deepseek-v3.1-250821")
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
                    "你是专业健身动作教练，基于系统提供的结构化反馈数据，"
                    "用中文给出语言流畅、鼓励性强的训练建议。"
                    "不要添加系统未提及的问题，不要编造数据。"
                    "重点放在：1)肯定优点 2)解释问题原因 3)给出可执行的改进方法。"
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
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
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
    """从统一反馈格式构建 prompt。

    统一反馈格式由 unified_feedback_service.format_for_ai() 生成：
    - errors: 主要问题列表
    - feedbacks: 改进建议列表
    - metrics: 关键指标
    - score: 综合评分
    - level: 等级
    - total_reps/valid_reps: 动作次数统计
    """
    exercise = payload.get("exercise", "squat")
    errors = payload.get("errors", [])
    feedbacks = payload.get("feedbacks", [])
    metrics = payload.get("metrics", {})
    score = payload.get("score", 0)
    level = payload.get("level", "unknown")
    total_reps = payload.get("total_reps", 0)
    valid_reps = payload.get("valid_reps", 0)

    # 构建结构化提示
    sections = [
        f"【动作类型】{exercise}",
        f"【完成情况】完成 {total_reps} 次，有效 {valid_reps} 次，综合评分 {score} 分（{level}）",
    ]

    if errors:
        sections.append(f"【检测到的问题】{'; '.join(errors)}")
    else:
        sections.append("【检测到的问题】无明显问题")

    if feedbacks:
        sections.append(f"【系统建议】{'; '.join(feedbacks)}")

    if metrics:
        metrics_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        sections.append(f"【关键指标】{metrics_str}")

    sections.append("\n请基于以上数据，输出一份专业的动作评估与改进建议：")
    sections.append("1. 【整体评价】先肯定做得好的地方")
    sections.append("2. 【主要问题】解释检测到的具体问题及可能原因")
    sections.append("3. 【改进建议】给出可执行的改进方法（用有序列表）")
    sections.append("4. 【下次训练重点】用1-2句话总结优先级")

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
