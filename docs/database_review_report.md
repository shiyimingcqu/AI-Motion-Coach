# 数据库代码审查与改进报告

> **项目**: 运动姿态评估与纠错系统 (yundongzitaipinggu)
> **审查日期**: 2026-06-30
> **审查范围**: 后端全部数据库相关代码

---

## 一、项目数据库技术栈概览

| 项目 | 详情 |
|------|------|
| 数据库 | 开发环境 SQLite / 生产环境 MySQL 8.4 |
| ORM | SQLAlchemy 2.0.45 |
| MySQL 驱动 | PyMySQL 1.1.1 |
| 迁移工具 | Alembic 1.13.1（已声明但**完全未配置**） |
| 缓存/队列 | Redis 7.2（Celery broker） |

---

## 二、问题清单（按严重程度排序）

### 🔴 严重（P0）

#### 1. 缺少数据库事务错误处理与回滚

**位置**: 全部数据库写入操作（`auth.py`, `admin.py`, `session_service.py`, `init_db.py` 等）

**问题**: 所有 `db.commit()` 调用都没有 `try/except` 捕获异常并执行 `db.rollback()`。如果 commit 失败（如约束冲突、连接断开），会话将处于不一致状态，后续操作可能产生脏数据。

**当前代码模式**:
```python
db = SessionLocal()
try:
    db.add(user)
    db.commit()       # 如果这里抛异常...
    db.refresh(user)
finally:
    db.close()        # ...只关闭了连接，没有 rollback
```

**改进建议**:
```python
db = SessionLocal()
try:
    db.add(user)
    db.commit()
    db.refresh(user)
except Exception:
    db.rollback()
    raise
finally:
    db.close()
```

**影响文件**:
- `backend/app/api/routes/auth.py` — register, login, update_profile, change_password
- `backend/app/api/routes/admin.py` — update_user, delete_user
- `backend/app/services/session/session_service.py` — create_session, delete_session
- `backend/app/services/task/task_service.py` — create_task, update_task
- `backend/app/db/init_db.py` — _create_default_users, _seed_exercises

---

#### 2. Alembic 数据库迁移完全未配置

**位置**: `backend/alembic/` 目录

**问题**: Alembic 在 `requirements.txt` 中声明了依赖，但 `alembic/` 目录下只有一个 README 占位文件，缺少 `alembic.ini`、`env.py` 和版本迁移脚本。当前 schema 管理完全依赖：
- `Base.metadata.create_all()` — 只能创建新表，**无法修改已有表结构**
- `init_db.py` 中的手动 `ALTER TABLE` — 脆弱、不可逆、难以追踪

**风险**: 生产环境中 schema 变更无法追踪、无法回滚、无法协作。多人开发时 schema 会漂移。

**改进建议**: 执行 `alembic init alembic`，配置 `alembic.ini` 和 `env.py` 关联 SQLAlchemy models，生成初始迁移脚本。后续所有 schema 变更通过 `alembic revision --autogenerate` 管理。

---

### 🟠 中等（P1）

#### 3. Dashboard/Report 聚合查询在内存中完成

**位置**:
- `backend/app/api/routes/dashboard.py` 第 26-55 行
- `backend/app/services/report/report_service.py` 第 19-44 行

**问题**: 先 `query.all()` 加载全部 session 记录到内存，再用 Python 循环计算 `sum()`、`len()`、平均值、趋势。当 sessions 表数据量增长后（数千到数万条），会有严重的性能问题和内存消耗。

**当前代码**:
```python
sessions = query.all()                          # 全部加载到内存
avg_score = sum(s.average_score for s in sessions) / total  # Python 层计算
total_duration = sum(s.duration_seconds for s in sessions)  # Python 层计算
```

**改进建议**: 使用 SQL 聚合函数，让数据库完成计算：
```python
from sqlalchemy import func

# 聚合统计
stats = db.query(
    func.count(SessionORM.id).label("total"),
    func.avg(SessionORM.average_score).label("avg_score"),
    func.sum(SessionORM.duration_seconds).label("total_duration"),
    func.sum(SessionORM.total_count).label("total_count"),
    func.sum(SessionORM.valid_count).label("valid_count"),
).filter(...).first()

# 按天分组趋势
trend = db.query(
    func.date(SessionORM.created_at).label("day"),
    func.avg(SessionORM.average_score).label("avg_score"),
).filter(...).group_by("day").order_by("day").limit(7).all()
```

---

#### 4. 数据库会话管理不一致

**位置**: 全部路由文件

**问题**: 项目中存在两种获取数据库会话的方式，且大多数路由没有使用 FastAPI 依赖注入：

- `deps.py` 定义了 `get_db()` 依赖注入（推荐方式），但几乎没有路由使用它
- 多数路由直接调用 `SessionLocal()` + `try/finally: db.close()`
- `auth.py` 甚至自定义了 `_get_db()` 辅助函数（第 19-23 行），绕过了依赖注入

**风险**: 代码重复、容易遗漏错误处理、无法利用 FastAPI 的依赖注入优势（如测试时替换数据库）。

**改进建议**: 全部路由统一使用 `Depends(get_db)`：
```python
@router.post("/register")
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    # 直接使用 db，无需手动 close
    ...
```

---

#### 5. `updated_at` 字段缺少自动更新机制

**位置**: `backend/app/models/entities.py`

**问题**: `ExerciseORM`、`ExerciseRuleORM`、`AnalysisTaskORM` 等模型都有 `updated_at` 字段，但只在 Python 代码中手动更新（如 `exercises.py` 第 90-91 行）。如果开发者忘记手动赋值，`updated_at` 不会反映真实更新时间。

**当前代码**:
```python
updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
# 没有 onupdate
```

**改进建议**:
```python
updated_at = Column(
    DateTime,
    default=lambda: datetime.now(timezone.utc),
    onupdate=lambda: datetime.now(timezone.utc),  # 每次 UPDATE 自动刷新
    nullable=False,
)
```

---

#### 6. `admin.py` 的 `update_user` 接受裸 dict 无验证

**位置**: `backend/app/api/routes/admin.py` 第 32 行

**问题**: `data: dict` 直接接受未验证的字典数据，没有使用 Pydantic 模型。虽然有 `if "role" in data` 做字段检查，但缺少类型验证、枚举值验证。攻击者可以传入任意键值对。

**当前代码**:
```python
@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: dict,                    # 无验证！
    ...
):
    if "role" in data:
        user.role = data["role"]    # 可以是任意字符串
```

**改进建议**:
```python
class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in ("user", "admin"):
            raise ValueError("role 必须是 user 或 admin")
        return v

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    ...
):
    if request.role is not None:
        user.role = request.role
    if request.is_active is not None:
        user.is_active = request.is_active
```

---

### 🟡 低（P2）

#### 7. `sessions` 表存在冗余字段 `exercise` 和 `exercise_id`

**位置**: `backend/app/models/entities.py` 第 181-182 行

**问题**: `sessions` 表同时有 `exercise`（String，旧兼容字段）和 `exercise_id`（FK）。两个字段可能指向不同动作，导致数据不一致。`init_db.py` 中的 `_migrate_legacy_schema()` 也是为了兼容这个旧字段。

**改进建议**: 长期规划移除 `exercise` 字段，统一使用 `exercise_id` 外键关联。在 Alembic 迁移中先做数据回填，再删除旧字段。

---

#### 8. `analysis_events` 和 `exercise_rules` 表已定义但未被使用

**位置**: `backend/app/models/entities.py` 第 101-244 行

**问题**: `AnalysisEventORM` 和 `ExerciseRuleORM` 已完整定义，但全代码库中没有任何代码实际写入或查询这两个表。它们会被 `create_all()` 创建但始终为空。

**改进建议**: 如果是规划中的功能，在文档中标注为 "planned, not yet implemented"。如果不会使用，移除模型定义避免混淆。

---

#### 9. SQLite 与 MySQL 的 ALTER TABLE 兼容性问题

**位置**: `backend/app/db/init_db.py` 第 178-191 行

**问题**: `_migrate_legacy_schema()` 使用 `ALTER TABLE sessions ADD COLUMN user_id INTEGER`，这在 MySQL 中不会自动添加外键约束。且 SQLite 的 ALTER TABLE 能力有限（不能修改列类型、不能删除列）。这种手动迁移方式在两个数据库间行为不一致。

**改进建议**: 迁移到 Alembic 后，移除 `_migrate_legacy_schema()` 函数，由 Alembic 统一管理 schema 变更。

---

#### 10. `create_session` 未设置 `exercise_id` 外键

**位置**: `backend/app/services/session/session_service.py` 第 53-63 行

**问题**: 创建 session 时只设置了 `exercise`（字符串字段），没有设置 `exercise_id`（外键字段）。这意味着 `exercise_id` 始终为 NULL，外键关系形同虚设，无法做 JOIN 查询。

**改进建议**: 在创建 session 时根据 `exercise` 字符串查询对应的 `ExerciseORM`，设置 `exercise_id`：
```python
exercise_obj = db.query(ExerciseORM).filter(ExerciseORM.key == exercise).first()
session = SessionORM(
    ...
    exercise=exercise,
    exercise_id=exercise_obj.id if exercise_obj else None,
)
```

---

#### 11. `session_service.list_sessions` 不接受 `user_id` 过滤

**位置**: `backend/app/services/session/session_service.py` 第 11-25 行

**问题**: `list_sessions()` 方法只接受 `limit` 和 `offset`，不支持按 `user_id` 过滤。`sessions.py` 路由中的 `list_sessions` 没有使用 service 层，而是直接操作数据库，绕过了服务层抽象。

**改进建议**: 在 service 层方法中增加过滤参数，让路由层调用 service 层而不是直接操作数据库。

---

#### 12. `session_service.get_session` 和 `delete_session` 打开两次数据库会话

**位置**: `backend/app/api/routes/sessions.py` 第 100-112 行

**问题**: `delete_session` 路由先调用 `session_service.get_session(session_id)` 查询一次（打开一个 db 会话并关闭），再调用 `session_service.delete_session(session_id)` 删除（又打开一个 db 会话并关闭）。两次独立的会话之间没有事务一致性保证。

**改进建议**: 在 service 层提供 `get_and_delete_session` 方法，在单个会话中完成查询+删除。

---

## 三、改进优先级建议

| 优先级 | 问题 | 工作量 | 建议 |
|--------|------|--------|------|
| **P0** | 事务回滚缺失 | 小 | 立即修复，统一添加 `except: db.rollback()` |
| **P0** | Alembic 未配置 | 中 | 尽快配置，生成初始迁移 |
| **P1** | 内存聚合查询 | 中 | 改为 SQL 聚合 |
| **P1** | 会话管理不一致 | 中 | 统一使用 `Depends(get_db)` |
| **P1** | `updated_at` 自动更新 | 小 | 添加 `onupdate` 参数 |
| **P1** | admin 接口缺少验证 | 小 | 添加 Pydantic 模型 |
| **P2** | 冗余字段 `exercise` | 大 | 需数据迁移，长期规划 |
| **P2** | 未使用的表 | 小 | 标注或移除 |
| **P2** | `exercise_id` 未设置 | 小 | 创建 session 时回填 |
| **P2** | service 层不完整 | 中 | 补充过滤参数 |

---

## 四、总结

项目数据库层面整体架构合理（SQLAlchemy ORM + 模型设计清晰），但存在以下核心问题：

1. **事务安全**：缺少 rollback，有脏数据风险
2. **迁移管理**：Alembic 形同虚设，schema 变更不可控
3. **查询性能**：大量内存聚合，数据量增长后会成为瓶颈
4. **代码一致性**：数据库会话获取方式不统一，service 层不完整

建议按优先级从 P0 开始逐步修复。P0 问题工作量小但风险高，应优先处理。
