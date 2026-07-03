from sqlalchemy import inspect, text

from app.db.session import engine
from app.core.security import get_password_hash
from app.models.entities import Base, UserORM, ExerciseORM, ReferenceVideoORM

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    Session = None


_SEED_EXERCISES = [
    {
        "key": "squat",
        "name": "深蹲",
        "category": "下肢力量",
        "level": "中级",
        "duration": "12 分钟",
        "description": "双脚与肩同宽，保持背部挺直，屈膝下蹲至大腿与地面平行，然后站起。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "下蹲深度不足,膝盖内扣",
        "accent": "#22c55e",
    },
    {
        "key": "push_up",
        "name": "俯卧撑",
        "category": "上肢力量",
        "level": "中级",
        "duration": "10 分钟",
        "description": "双手撑地与肩同宽，保持身体直线，屈肘下降至胸部近地，然后推起。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "手臂未伸直,身体塌腰",
        "accent": "#0ea5e9",
    },
    {
        "key": "jumping_jack",
        "name": "开合跳",
        "category": "心肺训练",
        "level": "初级",
        "duration": "8 分钟",
        "description": "双脚向外跳开同时双臂举过头顶，然后跳回并放下手臂，保持节奏。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "节奏过快,手脚幅度不足",
        "accent": "#f59e0b",
    },
    {
        "key": "plank",
        "name": "平板支撑",
        "category": "核心稳定",
        "level": "高级",
        "duration": "6 分钟",
        "description": "前臂撑地，身体从肩到踝保持一条直线，收紧核心保持稳定。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "髋部下沉,肩肘未对齐",
        "accent": "#14b8a6",
    },
    {
        "key": "lunge",
        "name": "弓步蹲",
        "category": "下肢力量",
        "level": "中级",
        "duration": "10 分钟",
        "description": "向前跨出一大步，屈膝下蹲至前后腿均呈90度，然后站起换腿。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "膝盖超过脚尖,身体前倾",
        "accent": "#8b5cf6",
    },
    {
        "key": "burpee",
        "name": "波比跳",
        "category": "全身",
        "level": "高级",
        "duration": "8 分钟",
        "description": "从站立下蹲至双手撑地，双脚后跳成俯卧撑姿势，再跳回并向上跃起。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "动作不连贯,核心松散",
        "accent": "#ef4444",
    },
    {
        "key": "mountain_climber",
        "name": "登山跑",
        "category": "核心稳定",
        "level": "中级",
        "duration": "8 分钟",
        "description": "俯卧撑姿势，交替提膝向胸部靠拢，保持核心收紧和节奏。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "臀部抬高,节奏不稳",
        "accent": "#f97316",
    },
    {
        "key": "pull_up",
        "name": "引体向上",
        "category": "上肢力量",
        "level": "高级",
        "duration": "10 分钟",
        "description": "双手正握横杆与肩同宽，背部发力拉起身体至下巴过杆，缓慢下降。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "摆动借力,下降过快",
        "accent": "#06b6d4",
    },
    {
        "key": "dumbbell_curl",
        "name": "哑铃弯举",
        "category": "上肢力量",
        "level": "初级",
        "duration": "8 分钟",
        "description": "双手持哑铃，上臂固定，前臂向上弯举至顶峰收缩，缓慢下放。",
        "modes": "视频上传分析",
        "errors": "身体晃动,肘部前移",
        "accent": "#ec4899",
    },
    {
        "key": "dumbbell_press",
        "name": "哑铃推举",
        "category": "上肢力量",
        "level": "中级",
        "duration": "10 分钟",
        "description": "坐姿或站姿，双手持哑铃从肩部向上推举至手臂伸直，控制下放。",
        "modes": "视频上传分析",
        "errors": "腰部反弓,手臂未完全伸直",
        "accent": "#a855f7",
    },
    {
        "key": "high_knees",
        "name": "高抬腿",
        "category": "心肺训练",
        "level": "初级",
        "duration": "6 分钟",
        "description": "原地交替提膝至大腿与地面平行，配合摆臂，保持快速节奏。",
        "modes": "摄像头实时检测,视频上传分析",
        "errors": "节奏不稳,膝盖抬起高度不足",
        "accent": "#eab308",
    },
    {
        "key": "russian_twist",
        "name": "俄罗斯转体",
        "category": "核心稳定",
        "level": "中级",
        "duration": "8 分钟",
        "description": "坐姿屈膝，上身稍后仰，双手合十左右旋转躯干，核心持续收紧。",
        "modes": "视频上传分析",
        "errors": "身体晃动,背部未挺直",
        "accent": "#f97316",
    },
    {
        "key": "glute_bridge",
        "name": "臀桥",
        "category": "下肢力量",
        "level": "初级",
        "duration": "8 分钟",
        "description": "仰卧屈膝，臀部发力向上抬起至肩-髋-膝成直线，顶峰收缩后缓慢下放。",
        "modes": "视频上传分析",
        "errors": "腰部代偿,抬臀高度不足",
        "accent": "#14b8a6",
    },
]


def init_db():
    """初始化数据库：创建表并添加默认账号"""
    if engine is None or Base is None or Session is None:
        return

    # 创建所有表（users + exercises + sessions + …）
    Base.metadata.create_all(bind=engine)
    _migrate_legacy_schema()

    # 创建默认账号
    db = Session(bind=engine)
    try:
        _create_default_users(db)
        _seed_exercises(db)
    finally:
        db.close()


def _migrate_legacy_schema():
    """Patch old SQLite schemas so newer ORM fields don't crash at runtime."""
    inspector = inspect(engine)

    if "sessions" not in inspector.get_table_names():
        return

    session_columns = {column["name"] for column in inspector.get_columns("sessions")}
    with engine.begin() as connection:
        if "user_id" not in session_columns:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN user_id INTEGER"))
        if "calories_burned" not in session_columns:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN calories_burned FLOAT DEFAULT 0"))
        if "evaluation_json" not in session_columns:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN evaluation_json TEXT"))
        if "feedback_summary" not in session_columns:
            connection.execute(text("ALTER TABLE sessions ADD COLUMN feedback_summary TEXT"))

    # Add camera_view column to analysis_tasks
    if "analysis_tasks" in inspector.get_table_names():
        task_columns = {column["name"] for column in inspector.get_columns("analysis_tasks")}
        if "camera_view" not in task_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE analysis_tasks ADD COLUMN camera_view VARCHAR(16) DEFAULT 'front'"))


def _create_default_users(db: Session):
    """如果用户表为空，创建默认管理员和普通用户"""
    existing_user = db.query(UserORM).first()
    if existing_user is not None:
        return

    default_users = [
        {
            "username": "admin",
            "password": "admin123",
            "role": "admin",
        },
        {
            "username": "user",
            "password": "user123",
            "role": "user",
        },
    ]

    for user_data in default_users:
        user = UserORM(
            username=user_data["username"],
            hashed_password=get_password_hash(user_data["password"]),
            role=user_data["role"],
        )
        db.add(user)

    db.commit()


def _seed_exercises(db: Session):
    """如果动作库为空，插入默认动作；已有数据则补充缺失的动作"""
    for data in _SEED_EXERCISES:
        existing = db.query(ExerciseORM).filter(ExerciseORM.key == data["key"]).first()
        if existing is None:
            ex = ExerciseORM(**data)
            db.add(ex)

    db.commit()
