# 运动姿态评估与纠错系统 — 项目记忆

## 项目架构
- **后端**: FastAPI + SQLAlchemy (SQLite) + MediaPipe + OpenCV
- **前端**: Vue 3 + Vite + MediaPipe PoseLandmarker + WebSocket
- **分析器模式**: 策略模式，BaseExerciseAnalyzer 基类，每个动作独立分析器

## 支持的动作（8 种）
深蹲(squat)、俯卧撑(push_up)、开合跳(jumping_jack)、平板支撑(plank)、
弓步蹲(lunge)、臀桥(glute_bridge)、高抬腿(high_knees)、波比跳(burpee)

## DTW 模板评分
- 所有分析器均基于 SquatAnalyzer 的 DTW 评分模式实现
- 评分公式：DTW 60% + 关键姿态 30% + 稳定性 10%
- 模板文件位于 backend/app/templates/*.json
- TemplateService 的 _find_template_file 支持 3 种命名模式

## 关键文件
- 分析器注册：backend/app/services/analysis/analyzers/registry.py
- 模板服务：backend/app/services/analysis/template_service.py
- 实时路由：backend/app/api/routes/realtime.py
- 前端实时：frontend/src/views/RealtimeDetectView.vue
- 前端 Store：frontend/src/stores/training.ts
- 种子数据：backend/app/db/init_db.py（8 种动作）

## 小程序端
- 技术栈：原生微信小程序 (WXML/WXSS/JS)
- 57+ 个文件，8 个页面（登录、首页 dashboard、动作库 list/detail、训练 training、结果 result、报告 reports、我的 profile）+ 4 个组件
- 认证：wx.login() → POST /api/auth/wechat-login → JWT
- 姿态检测：Camera 帧 → base64 → POST /api/realtime/pose-detect → 关键点 → WebSocket /api/realtime/pose → 评分 → Canvas 骨架
- 后端新增端点：
  - POST /api/auth/wechat-login（微信 code → openid → JWT）
  - POST /api/realtime/pose-detect（base64 图片帧 → MediaPipe 33 关键点）
- 后端模型修改：UserORM 新增 openid 字段，hashed_password 改为 nullable
- 视觉设计：主色 `#4f8cff`，圆角 16/20/28rpx，柔和卡片（白底 + 浅阴影 + 顶部彩色描边）
- 图表：折线图 / 雷达图通过 `rich-text` 节点注入 SVG 字符串实现
- WebSocket `analysis` 消息兼容多种字段名：`knee_angle`/`hip_angle`/`torso_angle` 或 `metrics.{knee,hip,torso}`
