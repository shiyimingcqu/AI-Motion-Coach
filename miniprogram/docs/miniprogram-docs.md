# 🏃 运动姿态评估与纠错系统 - 微信小程序功能文档

## 项目概述

基于 MediaPipe Pose + Three.js + Vue + 微信小程序的运动姿态评估系统。用户通过手机摄像头拍摄训练动作，系统实时识别骨骼关键点、评分、计数、纠错。

---

## 一、全局架构

### 技术栈
- **前端框架**：微信原生小程序
- **后端 API**：FastAPI（Python）
- **姿态识别**：MediaPipe Pose Landmarker
- **3D 渲染**：Three.js（Web 端）
- **实时通信**：WebSocket（训练评分）

### 后端地址
| 环境 | 地址 |
|------|------|
| 开发工具 | `http://127.0.0.1:8000` |
| 手机热点 | `http://192.168.43.113:8000` |

配置文件位置：`utils/constants.js`（修改 `API_BASE_HOST`）

### 登录体系
- **微信静默登录**：`wx.login()` → `POST /api/auth/wechat-login` → JWT
- **账号密码**：`POST /api/auth/login` → JWT
- Token 有效期 6 天，存 localStorage

---

## 二、页面功能详解

### 1. 登录页 `pages/login/`

| 功能 | 说明 |
|------|------|
| 微信一键登录 | `wx.login()` → 调后端换 JWT，成功后跳首页 |
| 账号密码登录 | 用户名 + 密码，`POST /api/auth/login` |
| 自动登录 | `onLoad` 检查缓存 token，有效则直接跳首页 |

**API**：`POST /api/auth/wechat-login`、`POST /api/auth/login`

### 2. 首页 `pages/dashboard/`

| 功能 | 说明 |
|------|------|
| 今日训练统计 | `GET /api/dashboard/stats` → 今日次数、平均分 |
| 本周训练数 | 本周总训练次数 |
| 推荐训练 | 随机展示 6 个动作的其一，点击跳评估列表 |
| 快速入口 | 今日训练/历史记录等 |

**API**：`GET /api/dashboard/stats`

### 3. 评估列表 `pages/exercises/list`

动作选择页，列出声明的所有动作（深蹲、俯卧撑、开合跳、平板支撑等 14 种）。
选择后进入训练页。

### 4. 训练页 `pages/training/` 🎯 **核心**

| 功能 | 说明 |
|------|------|
| 摄像头捕捉 | 实时帧捕获 |
| 姿态检测 | 帧 → POST 后端 → MediaPipe 关键点 |
| 实时评分 | `WebSocket` 实时评分推送 |
| 自动计数 | 按动作阶段（如深蹲：站立→下蹲→最低→起身）自动计次 |
| 错误检测 | 实时标记问题（如膝盖内扣、深度不足） |
| 引导提示 | 显示当前阶段 + 可视化指引 |

**场景值传入**：`OPTIONS.exercise` 指定动作类型

**API**：
- `POST /api/pose-detect` — 单帧姿态检测
- `WebSocket /api/ws/score` — 实时评分
- `POST /api/sessions` — 保存训练记录

### 5. 训练结果页 `pages/result/` 🎯 **核心**

| 功能 | 说明 |
|------|------|
| 总体评分 | 综合评分 + 等级显示 |
| 阶段概览 | 动作流程各阶段评分 |
| 问题清单 | 自动列出的错误/改进项，含严重程度（高/中/低） |
| 逐条纠正 | 每个问题对应改进建议 |
| AI 建议 | 轮询 `GET /api/ai-advice` 获取 AI 生成的训练建议 |
| 分享卡片 | 6 张背景图随机选取，生成分享图 |

**问题分类**：
- 深度相关：下蹲深度不足/偏深/不稳定
- 姿态相关：躯干前倾、膝盖内扣、左右不对称
- 节奏相关：速度偏快、节奏不稳定

**API**：
- `GET /api/sessions/:id` — 获取当次训练数据
- `GET /api/ai-advice/:session_id` — 获取 AI 建议（轮询，最长 90s）

### 6. 训练记录页 `pages/reports/`

| 功能 | 说明 |
|------|------|
| 训练列表 | 按时间倒序展示所有训练记录 |
| 训练详情 | 点击进入结果页查看详细评估 |

### 7. 个人中心 `pages/profile/`

| 功能 | 说明 |
|------|------|
| 个人统计 | 总训练次数、平均分、总时长 |
| 本周趋势 | 7 天分数趋势图（SVG 绘制） |
| 近期记录 | 最近的 7 条训练记录 |
| 荣誉数据 | 最佳成绩、连续天数、待改进项 |

**API**：`GET /api/dashboard/stats`、`GET /api/sessions`

### 8. 视频上传页 `pages/video-upload/`

| 功能 | 说明 |
|------|------|
| 视频选择 | 从相册选择训练视频 |
| 视频上传 | `POST /api/videos/upload` 上传到后端 |

### 9. Web 扫码登录页 `pages/web-login/`

Web 端微信扫码登录的中转页：
- 扫码 → 读取 `scene`（`web_login=ticket`）
- 自动 `wx.login()` → `POST /api/wechat/web-login/login`
- Web 端轮询到 JWT → 自动跳转首页

---

## 三、API 接口总览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/wechat-login` | 微信静默登录 |
| POST | `/api/auth/login` | 账号密码登录 |
| GET | `/api/auth/me` | 获取当前用户信息 |
| GET | `/api/dashboard/stats` | 首页/个人中心统计 |
| POST | `/api/pose-detect` | 单帧姿态检测 |
| WS | `/api/ws/score` | WebSocket 实时评分 |
| GET | `/api/sessions` | 训练记录列表 |
| POST | `/api/sessions` | 保存训练记录 |
| GET | `/api/sessions/:id` | 训练记录详情 |
| GET | `/api/ai-advice/:session_id` | AI 训练建议 |
| POST | `/api/videos/upload` | 视频上传 |
| GET | `/api/wechat/web-login/ticket` | 获取登录 ticket |
| GET | `/api/wechat/web-login/qrcode/:ticket` | 获取登录小程序码 |
| POST | `/api/wechat/web-login/login` | 扫码登录确认 |

---

## 四、支持的训练动作（14 种）

| 动作 | 类型 | 难度 | 监控指标 |
|------|------|------|---------|
| 深蹲 squat | 下肢力量 | 中级 | 膝角、髋角、躯干倾斜角、左右膝差 |
| 俯卧撑 push_up | 上肢力量 | 中级 | 肘角、肩角、身体直线角、髋部塌陷角 |
| 开合跳 jumping_jack | 心肺 | 初级 | 肩外展角、双腿夹角、手腕高度、脚踝距离 |
| 平板支撑 plank | 核心 | 高级 | 肩髋踝直线角、髋部角、颈部角 |
| 弓步蹲 lunge | 下肢力量 | 中级 | 膝角、髋角、躯干倾斜角、左右膝差 |
| 臀桥 glute_bridge | 下肢力量 | 初级 | 髋角、身体直线角 |
| 高抬腿 high_knees | 心肺 | 初级 | 抬膝高度、膝角 |
| 波比跳 burpee | 全身 | 高级 | 髋角、身体直线角、手腕高度 |
| 引体向上 pull_up | 上肢力量 | 高级 | 肩肘腕各角度 |
| 卧推 bench_press | 上肢力量 | 中级 | 肩肘腕各角度 |
| 杠铃深蹲 barbell_squat | 下肢力量 | 高级 | 膝角、髋角、躯干倾斜角 |
| 哑铃飞鸟 dumbbell_fly | 上肢力量 | 中级 | 肩肘腕各角度 |
| 高位下拉 lat_pulldown | 上肢力量 | 中级 | 肩肘腕各角度 |
| 哑铃推肩 dumbbell_shoulder_press | 上肢力量 | 中级 | 肩肘腕各角度 |

---

## 五、数据流

```
摄像头帧 → MediaPipe 关键点
    ↓
POST /api/pose-detect → 角度/指标计算
    ↓
WebSocket /api/ws/score → 实时评分 + 计数
    ↓
训练结束 → POST /api/sessions 保存
    ↓
GET /api/ai-advice → AI 建议生成
    ↓
训练记录可查询 → Web 端 3D 回放
```

---

## 六、附加说明

- **Web 端**：Vue3 项目，提供 3D 回放（Three.js 粒子人体）、训练记录管理、综合报告分析
- **微信小程序码**：`env_version` 可选 `develop` / `trial` / `release`，目前用 `develop`
- **路径**：`pages/web-login/web-login` 处理扫码登录
