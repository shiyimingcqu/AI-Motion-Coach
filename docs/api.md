# API 草案

## Health

- `GET /api/health`

## Exercises

- `GET /api/exercises`
- `POST /api/exercises/rules`

## Analysis

- `POST /api/videos/upload`
- `POST /api/analysis/tasks`
- `GET /api/analysis/tasks/{task_id}`

## Sessions

- `GET /api/sessions`
- `GET /api/sessions/{session_id}`

## Reports

- `GET /api/reports/personal`
- `GET /api/reports/class`

## Realtime

- `WS /api/realtime/pose`

实时响应示例：

```json
{
  "exercise": "squat",
  "stage": "down",
  "count": 12,
  "valid_count": 10,
  "score": 86,
  "errors": ["下蹲深度不足"],
  "features": {
    "depth_ratio": 0.18
  }
}
```
