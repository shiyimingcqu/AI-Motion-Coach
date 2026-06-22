# 工程化架构

系统采用模块化单体 API + 独立推理 Worker 的工程结构。前端负责用户操作和可视化，后端负责鉴权、任务、报表与实时通道，Worker 负责较重的视频分析任务。

```text
Vue3 Web
  -> FastAPI API Gateway
    -> auth / exercise / session / report / task services
    -> realtime WebSocket
    -> Redis + Celery
      -> Pose Inference Worker
    -> MySQL + storage
```

## 模块职责

- `api`：HTTP 与 WebSocket 入口。
- `services/pose`：姿态检测引擎抽象，默认 MediaPipe，预留 YOLO-Pose。
- `services/analysis`：角度计算、阶段识别、计数、评分和纠错。
- `services/task`：异步视频分析任务状态。
- `services/report`：个人和班级统计。
- `workers`：Celery 后台任务。

## 数据流

实时检测通过 WebSocket 输入关键点或帧数据，后端返回阶段、次数、评分和错误提示。视频上传先创建任务，Worker 后台处理并把结果写入数据库和对象存储。
