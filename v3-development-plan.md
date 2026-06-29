# 运动姿态评估与纠错系统 · v3 开发计划

> 版本：v3.0  
> 周期：预计 3 周  
> 定位：从"单动作演示"升级为"多动作评估平台"

---

## 一、当前状态总结

| 维度 | 状态 | 说明 |
|------|------|------|
| 深蹲实时检测 | ✅ 完成 | MediaPipe + WebSocket + DTW 模板评分 |
| 视频上传分析 | ✅ 完成 | OpenCV 逐帧处理 |
| 用户认证 | ✅ 完成 | JWT + 路由守卫 + 权限控制 |
| 动作库 | ✅ 完成 | 3D 环形画廊 + 网格视图 |
| 训练记录 | ⚠️ 半成品 | 内存存储，重启丢失 |
| 其他功能页 | ⚠️ 半成品 | 8 个页面有 UI 无真实数据 |
| 俯卧撑/开合跳/平板 | ❌ 未开始 | 仅注册了动作名称 |
| Celery 异步处理 | ❌ 未开始 | 占位代码 |
| YOLO-Pose 引擎 | ❌ 未开始 | 预留二期 |
| 数据库持久化 | ❌ 未开始 | Session/Task 存内存 |

---

## 二、整体架构变更

### 2.1 分析器架构：从单体到注册机制

**现状（v2）：**
```
ExerciseAnalyzer（一个类里写所有动作逻辑）
```

**目标（v3）：**
```
BaseExerciseAnalyzer（抽象基类）
├── SquatAnalyzer
├── PushUpAnalyzer
├── JumpingJackAnalyzer
└── PlankAnalyzer

AnalyzerRegistry（注册器，根据 exercise_type 路由）
```

文件结构：

```
backend/app/services/analysis/
├── analyzers/
│   ├── __init__.py
│   ├── base_analyzer.py       # 抽象基类 + 统一接口
│   ├── squat_analyzer.py      # 深蹲分析器（从原 ExerciseAnalyzer 迁移）
│   ├── push_up_analyzer.py    # 俯卧撑分析器（新增）
│   ├── jumping_jack_analyzer.py # 开合跳分析器（新增）
│   ├── plank_analyzer.py      # 平板支撑分析器（新增）
│   └── registry.py            # 注册器 + get_analyzer()
├── angle_calculator.py        # 角度计算工具函数（已有）
├── feedback_service.py        # 纠错建议生成（增强）
├── template_builder_service.py # 模板构建服务（增强）
└── exercise_analyzer.py       # 统一入口（保留，改为委托注册器）
```

### 2.2 BaseAnalyzer 统一接口

每个动作分析器实现以下方法：

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `extract_features(landmarks)` | MediaPipe 关键点字典 | 特征字典 | 计算当前帧的关节角度、距离、对称性 |
| `detect_phase(features, state)` | 特征 + 状态上下文 | 阶段字符串 | 识别当前处于动作的哪个阶段 |
| `score_frame(features, phase)` | 特征 + 阶段 | 分数 + 问题列表 | 单帧评分和问题检测 |
| `analyze_frame(landmarks, state)` | 关键点 + 状态 | 完整分析结果 | 组合以上三步，返回统一格式 |

返回格式统一：

```json
{
  "exercise_type": "push_up",
  "phase": "descending",
  "features": {
    "elbow_angle": 92.5,
    "body_line_angle": 176.2
  },
  "score": {
    "total": 78.5,
    "items": { "range": 82, "alignment": 75, "stability": 80 }
  },
  "issues": [
    { "type": "塌腰", "severity": "medium", "desc": "髋部下沉，身体不在一条直线" }
  ],
  "feedback": ["收紧核心，保持肩-髋-踝一条直线"]
}
```

---

## 三、Phase 1：重构分析器架构 + 多动作支持（第 1-5 天）

### 第 1 天：建立 BaseAnalyzer + AnalyzerRegistry

**任务清单：**

1. 新建 `analyzers/base_analyzer.py`
   - `BaseExerciseAnalyzer` 抽象类
   - 定义 `exercise_type` 类属性
   - `analyze_frame()` 模板方法（组合 extract → detect → score 三步）

2. 新建 `analyzers/registry.py`
   - `ANALYZER_REGISTRY` 字典
   - `get_analyzer(exercise_type: str)` 函数
   - 统一注册所有分析器实例

3. 新建 `analyzers/__init__.py`，导出所有分析器和注册器

4. 修改 `exercise_analyzer.py`
   - 去掉原有的 squat 硬编码逻辑
   - 改为委托 `get_analyzer().analyze_frame()`

**验证标准：** 导入不报错，`get_analyzer("squat")` 返回分析器实例

---

### 第 2 天：SquatAnalyzer 迁移

**任务清单：**

1. 新建 `analyzers/squat_analyzer.py`
   - 将 ExerciseAnalyzer 中 squat 相关的逻辑迁移过来
   - `extract_features()`：计算膝角、髋角、躯干角、对称性、重心偏移
   - `detect_phase()`：站立 → 下蹲 → 底部 → 起身 → 完成
   - `score_frame()`：幅度 40% + 躯干 20% + 稳定性 20% + 对称性 10% + 节奏 10%
   - 问题检测：膝内扣、骨盆前倾、重心偏移、肩不对称、后跟离地

2. 注册 SquatAnalyzer 到 AnalyzerRegistry

3. 测试：WebSocket 用 squat 类型连接，结果和之前一致

**评分维度详情：**

| 维度 | 权重 | 判定依据 |
|------|------|----------|
| 动作幅度 | 40% | 膝关节最大弯曲角度，≥90°为满分 |
| 躯干姿态 | 20% | 躯干前倾角度，≤20°为满分 |
| 稳定性 | 20% | 重心左右偏移量 |
| 左右对称性 | 10% | 左右膝、髋角度差 |
| 节奏控制 | 10% | 下蹲和起身帧数比，推荐 1:1~1:1.5 |

---

### 第 3 天：PushUpAnalyzer（俯卧撑）

**任务清单：**

1. 新建 `analyzers/push_up_analyzer.py`

**视角：侧面**

**关键角度计算：**
- 肘关节角：shoulder → elbow → wrist
- 肩关节角：hip → shoulder → elbow
- 身体直线角：shoulder → hip → ankle
- 髋部塌陷角：shoulder → hip → knee

**阶段识别：**

| 阶段 | 判断条件 |
|------|----------|
| `top_support`（顶部支撑） | 肘角 > 150°，身体直线 > 170° |
| `descending`（下降） | 肘角持续变小 |
| `bottom`（底部） | 肘角 ≤ 90° |
| `ascending`（上升） | 肘角持续变大 |
| `complete`（完成一次） | 回到顶部支撑 |

**常见问题检测：**
- 塌腰：身体直线角 < 165°，髋部下沉
- 撅臀：髋部过高，肩-髋-踝不成直线
- 肘部弯曲不足：最低点时肘角 > 110°
- 左右不对称：左右肩肘高度差 > 5cm
- 速度不稳定：同一组内下降时间波动 > 30%

**评分维度：**

| 维度 | 权重 | 说明 |
|------|------|------|
| 动作幅度 | 40% | 最低点时肘角 ≤ 90° 为满分 |
| 身体直线 | 30% | 全程肩-髋-踝直线角 |
| 稳定性 | 20% | 身体抖动幅度 |
| 节奏控制 | 10% | 下降/上升速度比 |

2. 注册 PushUpAnalyzer
3. 将对应的错误反馈中文文案写入 feedback_service

---

### 第 4 天：PlankAnalyzer（平板支撑）

**任务清单：**

1. 新建 `analyzers/plank_analyzer.py`

**视角：侧面**

**关键角度计算：**
- 身体直线角：shoulder → hip → ankle
- 髋部角度：shoulder → hip → knee
- 肩肘垂直度：shoulder 与 elbow 水平距离差
- 头颈姿态：ear → shoulder → hip
- 身体晃动方差：连续 N 帧关键点位置方差

**阶段识别（静态动作无需重复阶段）：**

| 阶段 | 判断条件 |
|------|----------|
| `ready`（准备） | 进入平板姿势，肩在手肘正上方 |
| `holding`（保持中） | 身体直线 > 165° |
| `unstable`（不稳定） | 身体直线 155°~165° 或晃动超限 |
| `collapsed`（动作失败） | 身体直线 < 155° 或保持 < 5 秒 |
| `finished`（结束） | 退出平板姿势 |

**常见问题检测：**
- 塌腰：髋部下沉，肩-髋-踝偏移超过 20°
- 撅臀：髋部过高
- 肩肘不齐：肩膀不在手肘正上方（水平偏差 > 10cm）
- 头颈姿态异常：头部过低或过高
- 身体晃动过大：关键点位置方差超限
- 坚持时间不足：少于设定目标时间

**评分维度：**

| 维度 | 权重 | 说明 |
|------|------|------|
| 身体直线 | 40% | 全程肩-髋-踝角度维持 |
| 核心稳定性 | 30% | 身体抖动幅度方差 |
| 肩肘位置 | 15% | 手肘在肩正下方的保持度 |
| 持续时间 | 15% | 坚持时间的评分比例 |

2. 注册 PlankAnalyzer
3. 由于 plank 是静态动作，模板不需要 DTW，改用**阈值区间评分**

---

### 第 5 天：JumpingJackAnalyzer（开合跳）

**任务清单：**

1. 新建 `analyzers/jumping_jack_analyzer.py`

**视角：正面**

**关键特征计算：**
- 双脚距离：left_ankle → right_ankle 的水平距离
- 手臂高度：手相对于肩/头的高度
- 手臂打开角：shoulder → elbow → wrist
- 腿部打开幅度：双脚距离 / 骨盆宽度
- 左右对称性：左右手高度差、左右脚距离差

**阶段识别：**

| 阶段 | 判断条件 |
|------|----------|
| `closed`（合拢） | 脚距 < 肩宽，手低于肩 |
| `opening`（打开） | 脚距变大，手上举 |
| `open_peak`（最大打开） | 脚距最大，手举过头顶 |
| `closing`（收回） | 脚距变小，手下落 |
| `complete`（完成一次） | 回到合拢状态 |

**常见问题检测：**
- 手臂未举过肩：手腕最高点低于肩
- 双脚打开不足：最大脚距 < 1.5× 肩宽
- 手脚不同步：脚和手未同时到达最大位置
- 左右不对称：左右手高度差 > 10cm
- 落地膝内扣：落地时膝角异常
- 节奏不稳定：相邻两次完成帧数差 > 30%

**评分维度：**

| 维度 | 权重 | 说明 |
|------|------|------|
| 手臂幅度 | 25% | 手臂是否充分举过头顶 |
| 腿部幅度 | 25% | 双脚是否充分打开 |
| 手脚同步 | 25% | 手脚是否同时到达最大打开 |
| 节奏稳定 | 15% | 每次完成的帧数一致性 |
| 左右对称 | 10% | 左右侧开合幅度一致 |

2. 注册 JumpingJackAnalyzer

---

## 四、Phase 2：API 接口 + 数据库持久化（第 6-8 天）

### 第 6 天：数据库建模

**任务清单：**

1. 在 `models/entities.py` 中新增 SQLAlchemy ORM 模型：

```python
class TrainingSessionORM(Base):
    __tablename__ = "training_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    exercise_type = Column(String, nullable=False)
    total_score = Column(Float, default=0)
    duration_seconds = Column(Integer, default=0)
    rep_count = Column(Integer, default=0)
    video_path = Column(String, nullable=True)
    annotated_video_path = Column(String, nullable=True)
    score_breakdown = Column(Text, nullable=True)  # JSON string
    error_summary = Column(Text, nullable=True)    # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("UserORM", backref="sessions")
```

2. 同步新建 `AnalysisTaskORM`、`ScoreTemplateORM`

3. 修改 `SessionService` / `TaskService`：从内存存储改为 SQLAlchemy CRUD

4. 运行 `Base.metadata.create_all()` 建表

---

### 第 7 天：数据接口补全

**新建接口：**

| 接口 | 方法 | 用途 |
|------|------|------|
| `/api/sessions` | GET | 分页查询训练记录（支持 search、exercise_type、date_from/date_to） |
| `/api/sessions/{id}` | GET | 单条会话详情 |
| `/api/sessions/{id}` | DELETE | 删除会话 |
| `/api/reports` | GET | 查询报告列表 |
| `/api/reports/{id}` | GET | 单份报告详情 |
| `/api/reports/{id}/export?format=pdf` | GET | 导出 PDF |
| `/api/feedback?session_id=` | GET | 某次训练的错误列表 |
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/users/{id}` | PUT | 修改用户 |
| `/api/admin/users/{id}` | DELETE | 删除用户 |
| `/api/admin/settings` | GET | 系统设置 |
| `/api/admin/settings` | PUT | 更新系统设置 |

---

### 第 8 天：前端 API 封装

**新增前端文件：**

| 文件 | 导出函数 |
|------|----------|
| `frontend/src/api/sessions.ts` | `getSessions()`, `getSession()`, `deleteSession()` |
| `frontend/src/api/reports.ts` | `getReports()`, `getReport()`, `exportReport()` |
| `frontend/src/api/feedback.ts` | `getErrorFeedbacks(sessionId)` |
| `frontend/src/api/admin.ts` | `getUsers()`, `updateUser()`, `deleteUser()`, `getSettings()`, `updateSettings()` |

**修改现有页面：**
- `DashboardView.vue` → 去掉所有 hardcoded demo data，改为调用 API
- `SessionsView.vue` → 接入真实分页和筛选
- `ReportsView.vue` → 接入报告列表

---

## 五、Phase 3：前端体验完善（第 9-11 天）

### 第 9 天：三态标准化

每个接入 API 的页面统一实现三种状态：

```vue
<template>
  <div v-if="loading">    <LoadingSkeleton /> </div>
  <div v-else-if="error">  <ErrorState :message="error" @retry="fetchData" /> </div>
  <div v-else-if="!data">  <EmptyState message="暂无数据" /> </div>
  <div v-else>             <!-- 正常内容 --> </div>
</template>
```

新建组件：
- `LoadingSkeleton.vue` — 骨架屏，匹配卡片/表格/图表三种布局
- `EmptyState.vue` — 空状态占位
- `ErrorState.vue` — 错误状态 + 重试按钮
- `Pagination.vue` — 分页组件

---

### 第 10 天：搜索与筛选对齐

统一所有列表页的搜索筛选体验：

| 页面 | 筛选维度 |
|------|----------|
| 训练记录 | 动作类型 + 时间范围 + 关键词 |
| 评估报告 | 动作类型 + 日期区间 + 评分范围 |
| 用户管理 | 角色 + 状态 + 关键词 |
| 动作库 | 部位 + 难度 + 关键词（已有） |

统一筛选栏组件 `FilterBar.vue`，复用各页面。

### 第 11 天：首页真实数据 + 导出 PDF

**首页 Dashboard API：**

| 接口 | 返回 |
|------|------|
| `GET /api/dashboard/stats` | 今日训练数、活跃用户、平均分、进步率 |
| `GET /api/dashboard/trend?days=7` | 7 天评分趋势 |
| `GET /api/dashboard/recent?limit=5` | 最近 5 条评估记录 |

**PDF 导出后端：**
- 使用 `reportlab` 生成评估报告 PDF
- 包含：基本信息、评分雷达图、错误列表、纠正建议
- 支持中文字体嵌入

---

## 六、Phase 4：收尾与发布（第 12-15 天，可选）

### 第 12 天：WebSocket 前端动作选择

- 前端 `RealtimeDetectView.vue` 增加动作选择器
- 选择动作后 WebSocket 带上 `exercise_type` 参数
- 根据动作类型切换阶段轴标签、问题卡片模板、纠正建议内容

### 第 13 天：管理员后台完善

- UserManagementView 接入真实增删改查
- SettingsView 接入真实系统配置
- 侧边栏清理重复链接

### 第 14 天：错误修复 + 边界处理

- WebSocket 断线重连
- 视频上传超时处理
- 大分辨率视频降采样
- 空状态页面覆盖

### 第 15 天：文档 + 演示准备

- API 文档更新
- 演示脚本准备（4 个动作各走一遍）
- 前后端打包部署验证

---

## 七、开发顺序建议

### 最优路线

```
第 1 天  → BaseAnalyzer + Registry 搭建
第 2 天  → SquatAnalyzer 迁移（验证架构）
第 3 天  → PushUpAnalyzer（复用 squat 的角度计算）
第 4 天  → PlankAnalyzer（不同逻辑，静态评分）
第 5 天  → JumpingJackAnalyzer（正面视角，手脚同步）
───────── 里程碑：4 个动作检测可跑通 ─────────
第 6 天  → 数据库建模 SessionORM
第 7 天  → API 接口层补全
第 8 天  → 前端 API 封装
───────── 里程碑：后端接口可用 ─────────
第 9 天  → 三态组件 + 分页组件
第 10 天 → 搜索筛选对齐
第 11 天 → 首页真实数据 + PDF 导出
───────── 里程碑：前台页面可展示真实数据 ─────────
第 12-15 天 → 收尾
```

### 最低可行版本（MVP）

如果时间有限，只做：

1. BaseAnalyzer + Registry + SquatAnalyzer 迁移（1 天）
2. PushUpAnalyzer（1 天）
3. 数据库 SessionORM 建表 + SessionService 迁移（1 天）
4. SessionsView 接入真实数据 + 首页 stats API（1 天）

4 天即可让项目从"只有深蹲"变成"双动作 + 数据能保存"。

---

## 八、技术债务清理

### 必须清理

| 项目 | 原因 |
|------|------|
| RealtimeDetectView.vue 中的乱码中文 | 编码问题导致显示 `????` |
| 侧边栏重复链接（/realtime 和 /rules 各出现两次） | 导航混乱 |
| exercies.ts 和 stores/training.ts 中重复的 Exercise 接口 | 类型不一致 |
| 硬编码密钥 `"pose-evaluation-secret-key-dev-only"` | 安全隐患 |

### 建议清理

| 项目 | 说明 |
|------|------|
| 统一的 Loading/Empty/Error 三态 | 体验一致性 |
| API client 添加拦截器日志 | 调试方便 |
| 前端路由统一添加 title meta | 页面标题支持 |

---

## 九、关键设计决策

### 1. 模板评分 vs 实时规则评分

对于 v3，建议 **实时检测用规则评分，事后生成报告用模板匹配**。

| 场景 | 方案 | 原因 |
|------|------|------|
| 实时检测 | 规则评分（阈值 + 角度） | 低延迟，可解释 |
| 视频分析 | 模板 DTW 匹配 | 更精确的帧对齐 |
| 离线报告 | 综合评分 | 结合规则和模板结果 |

### 2. WebSocket 协议

保持现有 JSON 帧协议不变，增加 `exercise_type` 字段：

```
客户端 → 服务端：
{ "type": "frame", "image_data": "base64...", "exercise_type": "push_up" }

服务端 → 客户端：
{ "type": "result", "phase": "descending", "score": { ... }, "issues": [...] }
```

### 3. 数据库选择

继续使用 SQLite（项目初期够用）。如果后续数据量大，可平滑迁移到 PostgreSQL：

- SQLAlchemy ORM 抽象了数据库差异
- 只需修改 `DATABASE_URL` 环境变量即可切换
- 当前 SQLite 路径保留在 `backend/` 目录

---

## 十、项目结构变化总览

### 新增文件

```
backend/
├── app/services/analysis/analyzers/
│   ├── __init__.py
│   ├── base_analyzer.py
│   ├── squat_analyzer.py
│   ├── push_up_analyzer.py
│   ├── jumping_jack_analyzer.py
│   ├── plank_analyzer.py
│   └── registry.py
├── app/services/analysis/template_loader.py
├── app/api/routes/admin.py
├── app/api/routes/feedback.py

frontend/src/
├── api/sessions.ts
├── api/reports.ts
├── api/feedback.ts
├── api/admin.ts
├── components/LoadingSkeleton.vue
├── components/EmptyState.vue
├── components/ErrorState.vue
├── components/Pagination.vue
└── components/FilterBar.vue
```

### 修改文件

```
backend/
├── app/services/analysis/exercise_analyzer.py    # 改为委托注册器
├── app/services/analysis/__init__.py              # 导出所有分析器
├── app/services/session/__init__.py               # SQLAlchemy 化
├── app/services/report/report_service.py          # 真实数据聚合
├── app/models/entities.py                         # 新增 ORM 模型
├── app/api/routes/analysis.py                     # 扩展 session/report 接口
├── app/api/routes/reports.py                      # 扩展报告接口
├── app/api/__init__.py                            # 注册新路由

frontend/src/
├── views/DashboardView.vue                        # 接入真实 API
├── views/SessionsView.vue                         # 接入真实 API
├── views/ReportsView.vue                          # 接入真实 API
├── views/ErrorFeedbackView.vue                    # 接入真实 API
├── views/RealtimeDetectView.vue                   # 动作类型选择
├── views/UserManagementView.vue                   # 接入真实 API
├── views/SettingsView.vue                         # 接入真实 API
├── App.vue                                        # 清理侧边栏导航
├── api/exercises.ts                               # 统一类型定义
└── stores/training.ts                             # 统一类型定义
```

---

## 附录：各动作分析器 API 对照表

| 方法 | SquatAnalyzer | PushUpAnalyzer | PlankAnalyzer | JumpingJackAnalyzer |
|------|---------------|----------------|---------------|---------------------|
| **视角** | 侧面/正面 | 侧面 | 侧面 | 正面 |
| **exercise_type** | `squat` | `push_up` | `plank` | `jumping_jack` |
| **阶段数** | 5 阶段 | 5 阶段 | 5 阶段 | 5 阶段 |
| **阶段类型** | 动态重复 | 动态重复 | 静态保持 | 动态重复 |
| **关键角度** | 膝、髋、躯干、踝 | 肘、肩、躯干、髋 | 肩-髋-踝、髋部 | 肩、肘、踝 |
| **评分维度数** | 5 | 4 | 4 | 5 |
| **问题类型数** | 5 | 5 | 5 | 6 |
| **模板适用性** | DTW ✅ | DTW ✅ | 阈值区间 | DTW ✅ |
