# 部署说明

开发环境可使用 Docker Compose：

```powershell
cd deploy
docker compose up --build
```

服务端口：

- 前端：`http://localhost:5173`
- API：`http://localhost:8000`
- MySQL：`localhost:3306`
- Redis：`localhost:6379`
- MinIO：`http://localhost:9001`
- Prometheus：`http://localhost:9090`
- Grafana：`http://localhost:3000`

本地无 Docker 时，可以分别启动：

```powershell
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

```powershell
cd frontend
npm install
npm run dev
```
