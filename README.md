# 运动姿态评估与纠错系统

面向健身、体育教学和训练评估场景的工程化运动姿态分析系统，支持姿态检测、动作计数、纠错提示和训练数据统计。

## 架构概览

本项目采用前后端分离与独立推理 Worker 架构：

- `frontend/`：Vue3 + Vite 管理工作台，提供实时检测、视频上传、训练记录、报表和规则配置页面。
- `backend/`：FastAPI API 网关，包含业务服务、姿态分析算法、任务管理、WebSocket 实时检测和 Worker 入口。
- `deploy/`：Docker Compose、Nginx、Prometheus、Grafana 等部署配置。
- `storage/`：本地开发环境的上传文件、分析结果和报告输出目录。
- `docs/`：架构、接口、算法和部署文档。

## 本地验证

核心算法测试不依赖第三方包：

```powershell
$env:PYTHONPATH='backend'
python -m unittest discover -s backend/tests -p "test_*.py"
```

## 完整后端依赖安装后可启动 API：

```powershell
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

## 前端启动：
### 首次启动：
```powershell
cd frontend
npm install
npm run dev
```
### 以后启动：
```powershell
cd frontend
npm run dev
```