# 数据库设计草案

建议表结构：

- `users`：用户、角色、密码摘要、所属班级。
- `exercise_rules`：动作类型、阈值、评分规则、提示模板。
- `analysis_tasks`：异步任务、状态、文件地址、错误原因。
- `training_sessions`：一次训练概要，包含动作、时长、次数、评分。
- `analysis_events`：关键错误事件、时间点、错误类型和关键帧。
- `reports`：导出报告记录。

首期代码使用内存服务保持接口形状，接入 SQLAlchemy 后再由 Alembic 管理迁移。
