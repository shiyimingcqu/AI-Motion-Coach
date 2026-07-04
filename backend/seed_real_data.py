"""向 MySQL 填充真实业务数据 — 模拟运动姿态评估系统的真实使用场景"""

import pymysql
import bcrypt
import json
import random
from datetime import datetime, timedelta

conn = pymysql.connect(
    host='localhost', port=3306,
    user='pose_app', password='pose_app_2026',
    database='pose_evaluation', charset='utf8mb4',
    autocommit=False
)
cur = conn.cursor()

now = datetime.utcnow()

# ============================================================
# 1. 清空旧数据（保留表结构）
# ============================================================
print("1. 清空旧数据...")
cur.execute("SET FOREIGN_KEY_CHECKS=0")
for table in ['analysis_events', 'reports', 'analysis_tasks', 'sessions', 'exercise_rules', 'exercises', 'users']:
    cur.execute(f"TRUNCATE TABLE `{table}`")
cur.execute("SET FOREIGN_KEY_CHECKS=1")
conn.commit()
print("   已清空所有表")

# ============================================================
# 2. users — 真实用户数据（6个用户）
# ============================================================
print("2. 插入用户数据...")
real_users = [
    # (username, password, role, is_active)
    ("admin", "admin123", "admin", 1),
    ("fuzhentian", "fzt20260630", "admin", 1),
    ("zhangminghao", "zmh20260630", "user", 1),
    ("liwenbo", "lwb20260630", "user", 1),
    ("wangjiaqi", "wjq20260630", "user", 1),
    ("chenyuhan", "cyh20260630", "user", 1),
]

for username, password, role, is_active in real_users:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    created = now - timedelta(days=random.randint(10, 30))
    cur.execute(
        "INSERT INTO users (username, hashed_password, role, is_active, created_at) VALUES (%s,%s,%s,%s,%s)",
        (username, hashed, role, is_active, created)
    )
conn.commit()
cur.execute("SELECT id, username, role FROM users ORDER BY id")
user_rows = cur.fetchall()
print(f"   插入 {len(user_rows)} 个用户:")
for uid, uname, role in user_rows:
    print(f"     id={uid}, username={uname}, role={role}")

# 用户 ID 映射
user_ids = {uname: uid for uid, uname, _ in user_rows}

# ============================================================
# 3. exercises — 13种运动动作（真实参数）
# ============================================================
print("\n3. 插入动作数据...")
exercises_data = [
    ("squat", "深蹲", "下肢力量", "中级", "12 分钟",
     "双脚与肩同宽，保持背部挺直，屈膝下蹲至大腿与地面平行，然后站起。注意膝盖不要超过脚尖，核心收紧保持稳定。",
     "摄像头实时检测,视频上传分析", "下蹲深度不足,膝盖内扣,背部弯曲", "#22c55e"),
    ("push_up", "俯卧撑", "上肢力量", "中级", "10 分钟",
     "双手撑地与肩同宽，保持身体从头到脚成一条直线，屈肘下降至胸部近地，然后推起。注意核心收紧不要塌腰。",
     "摄像头实时检测,视频上传分析", "手臂未伸直,身体塌腰,下降不到位", "#0ea5e9"),
    ("jumping_jack", "开合跳", "心肺训练", "初级", "8 分钟",
     "双脚向外跳开同时双臂举过头顶，然后跳回并放下手臂，保持节奏。注意手脚协调配合。",
     "摄像头实时检测,视频上传分析", "节奏过快,手脚幅度不足,手臂未伸直", "#f59e0b"),
    ("plank", "平板支撑", "核心稳定", "高级", "6 分钟",
     "前臂撑地，身体从肩到踝保持一条直线，收紧核心保持稳定。注意髋部不要下沉或翘起。",
     "摄像头实时检测,视频上传分析", "髋部下沉,肩肘未对齐,臀部翘起", "#14b8a6"),
    ("lunge", "弓步蹲", "下肢力量", "中级", "10 分钟",
     "向前跨出一大步，屈膝下蹲至前后腿均呈90度，然后站起换腿。注意前膝不要超过脚尖。",
     "摄像头实时检测,视频上传分析", "膝盖超过脚尖,身体前倾,后腿弯曲不足", "#8b5cf6"),
    ("burpee", "波比跳", "全身", "高级", "8 分钟",
     "从站立下蹲至双手撑地，双脚后跳成俯卧撑姿势，再跳回并向上跃起。注意动作连贯性。",
     "摄像头实时检测,视频上传分析", "动作不连贯,核心松散,俯卧撑不到位", "#ef4444"),
    ("mountain_climber", "登山跑", "核心稳定", "中级", "8 分钟",
     "俯卧撑姿势，交替提膝向胸部靠拢，保持核心收紧和节奏。注意臀部不要抬高。",
     "摄像头实时检测,视频上传分析", "臀部抬高,节奏不稳,提膝不足", "#f97316"),
    ("pull_up", "引体向上", "上肢力量", "高级", "10 分钟",
     "双手正握横杆与肩同宽，背部发力拉起身体至下巴过杆，缓慢下降。注意不要摆动借力。",
     "摄像头实时检测,视频上传分析", "摆动借力,下降过快,拉起不到位", "#06b6d4"),
    ("dumbbell_curl", "哑铃弯举", "上肢力量", "初级", "8 分钟",
     "双手持哑铃，上臂固定，前臂向上弯举至顶峰收缩，缓慢下放。注意肘部不要前移。",
     "视频上传分析", "身体晃动,肘部前移,下放过快", "#ec4899"),
    ("dumbbell_press", "哑铃推举", "上肢力量", "中级", "10 分钟",
     "坐姿或站姿，双手持哑铃从肩部向上推举至手臂伸直，控制下放。注意腰部不要反弓。",
     "视频上传分析", "腰部反弓,手臂未完全伸直,下放过快", "#a855f7"),
    ("high_knees", "高抬腿", "心肺训练", "初级", "6 分钟",
     "原地交替提膝至大腿与地面平行，配合摆臂，保持快速节奏。注意核心收紧。",
     "摄像头实时检测,视频上传分析", "节奏不稳,膝盖抬起高度不足,身体后仰", "#eab308"),
    ("russian_twist", "俄罗斯转体", "核心稳定", "中级", "8 分钟",
     "坐姿屈膝，上身稍后仰，双手合十左右旋转躯干，核心持续收紧。注意背部挺直。",
     "视频上传分析", "身体晃动,背部未挺直,转动幅度不足", "#f97316"),
    ("glute_bridge", "臀桥", "下肢力量", "初级", "8 分钟",
     "仰卧屈膝，臀部发力向上抬起至肩-髋-膝成直线，顶峰收缩后缓慢下放。注意不要腰部代偿。",
     "视频上传分析", "腰部代偿,抬臀高度不足,下放过快", "#14b8a6"),
]

for key, name, cat, lvl, dur, desc, modes, errors, accent in exercises_data:
    created = now - timedelta(days=30)
    updated = now - timedelta(days=random.randint(1, 10))
    cur.execute(
        "INSERT INTO exercises (`key`, name, category, level, duration, description, modes, errors, accent, is_active, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)",
        (key, name, cat, lvl, dur, desc, modes, errors, accent, created, updated)
    )
conn.commit()
cur.execute("SELECT id, `key` FROM exercises ORDER BY id")
exercise_rows = cur.fetchall()
print(f"   插入 {len(exercise_rows)} 个动作")
exercise_ids = {key: eid for eid, key in exercise_rows}

# ============================================================
# 4. exercise_rules — 评估规则（基于代码中的真实角度阈值）
# ============================================================
print("\n4. 插入评估规则数据...")
rules_data = [
    # (exercise_id, rule_key, name, metric, operator, threshold_min, threshold_max, score_weight, feedback_template, severity)
    # 深蹲规则
    (exercise_ids["squat"], "squat_knee_angle_bottom", "底部膝盖角度", "knee_angle", "range", 75.0, 110.0, 0.40,
     "深蹲底部膝盖角度应在75°-110°之间，当前{value}°，{suggestion}", "error"),
    (exercise_ids["squat"], "squat_hip_angle_bottom", "底部髋部角度", "hip_angle", "range", 70.0, 120.0, 0.25,
     "深蹲底部髋部角度应在70°-120°之间，当前{value}°，{suggestion}", "error"),
    (exercise_ids["squat"], "squat_trunk_angle", "躯干前倾角度", "trunk_angle", "range", 5.0, 35.0, 0.25,
     "躯干前倾角度应在5°-35°之间，当前{value}°，{suggestion}", "warning"),
    (exercise_ids["squat"], "squat_knee_symmetry", "膝盖对称性", "knee_symmetry_diff", "max", 0.0, 10.0, 0.10,
     "左右膝盖角度差应小于10°，当前差{value}°，注意对称发力", "warning"),
    # 俯卧撑规则
    (exercise_ids["push_up"], "pushup_elbow_angle_down", "下降肘部角度", "elbow_angle", "range", 70.0, 100.0, 0.35,
     "俯卧撑下降时肘部角度应在70°-100°之间，当前{value}°，{suggestion}", "error"),
    (exercise_ids["push_up"], "pushup_body_line", "身体直线度", "body_line_angle", "max", 0.0, 15.0, 0.30,
     "身体偏离直线应小于15°，当前偏离{value}°，注意收紧核心", "error"),
    (exercise_ids["push_up"], "pushup_hip_sag", "髋部下沉", "hip_sag", "max", 0.0, 12.0, 0.20,
     "髋部下沉应小于12°，当前下沉{value}°，避免塌腰", "warning"),
    (exercise_ids["push_up"], "pushup_symmetry", "左右对称性", "symmetry_diff", "max", 0.0, 10.0, 0.15,
     "左右肘部角度差应小于10°，当前差{value}°，注意对称发力", "warning"),
    # 开合跳规则
    (exercise_ids["jumping_jack"], "jj_spread_ratio", "开合幅度", "spread_ratio", "min", 1.5, None, 0.35,
     "手脚开合幅度应达到1.5倍肩宽以上，当前{value}，{suggestion}", "error"),
    (exercise_ids["jumping_jack"], "jj_arm_height", "手臂抬起高度", "avg_arm_height", "min", 0.05, None, 0.25,
     "手臂应举过头顶，当前抬起高度{value}，注意充分上举", "warning"),
    (exercise_ids["jumping_jack"], "jj_arm_sync", "手臂同步性", "arm_height_diff", "max", 0.0, 0.05, 0.20,
     "左右手臂高度差应小于0.05，当前差{value}，注意手脚同步", "warning"),
    (exercise_ids["jumping_jack"], "jj_leg_spread", "腿部张开角度", "leg_spread_angle", "min", 30.0, None, 0.20,
     "腿部张开角度应大于30°，当前{value}°，注意充分打开", "warning"),
    # 平板支撑规则
    (exercise_ids["plank"], "plank_body_line", "身体直线度", "body_line_angle", "max", 0.0, 10.0, 0.40,
     "身体偏离直线应小于10°，当前偏离{value}°，{suggestion}", "error"),
    (exercise_ids["plank"], "plank_hip_sag", "髋部下沉", "hip_sag", "max", 0.0, 12.0, 0.35,
     "髋部下沉应小于12°，当前下沉{value}°，注意收紧核心", "error"),
    (exercise_ids["plank"], "plank_neck_angle", "颈部角度", "neck_angle", "range", 150.0, 180.0, 0.25,
     "颈部角度应在150°-180°之间，当前{value}°，注意保持头部中立", "warning"),
    # 弓步蹲规则
    (exercise_ids["lunge"], "lunge_front_knee", "前膝角度", "front_knee_angle", "range", 80.0, 110.0, 0.35,
     "前膝角度应在80°-110°之间，当前{value}°，{suggestion}", "error"),
    (exercise_ids["lunge"], "lunge_back_knee", "后膝角度", "back_knee_angle", "range", 80.0, 120.0, 0.25,
     "后膝角度应在80°-120°之间，当前{value}°，注意后腿弯曲到位", "warning"),
    (exercise_ids["lunge"], "lunge_trunk", "躯干角度", "trunk_angle", "range", 0.0, 15.0, 0.25,
     "躯干前倾应小于15°，当前{value}°，保持上身直立", "warning"),
    (exercise_ids["lunge"], "lunge_knee_over_toe", "膝盖过脚尖", "knee_over_toe", "max", 0.0, 0.0, 0.15,
     "前膝不应超过脚尖，注意控制跨步距离", "error"),
    # 波比跳规则
    (exercise_ids["burpee"], "burpee_pushup_depth", "俯卧撑深度", "pushup_depth", "range", 70.0, 100.0, 0.30,
     "波比跳中俯卧撑下降肘部角度应在70°-100°之间，当前{value}°", "warning"),
    (exercise_ids["burpee"], "burpee_jump_height", "跳跃高度", "jump_height", "min", 0.1, None, 0.25,
     "向上跳跃高度应大于0.1，当前{value}，注意充分跳起", "warning"),
    (exercise_ids["burpee"], "burpee_core_stability", "核心稳定性", "core_stability", "max", 0.0, 15.0, 0.25,
     "核心偏离应小于15°，当前偏离{value}°，注意收紧核心", "warning"),
    (exercise_ids["burpee"], "burpee_continuity", "动作连贯性", "continuity_score", "min", 0.7, None, 0.20,
     "动作连贯性评分应大于0.7，当前{value}，注意动作衔接", "warning"),
    # 登山跑规则
    (exercise_ids["mountain_climber"], "mc_hip_height", "臀部高度", "hip_height", "max", 0.0, 0.1, 0.30,
     "臀部不应抬高超过0.1，当前{value}，保持身体平直", "error"),
    (exercise_ids["mountain_climber"], "mc_knee_height", "提膝高度", "knee_raise_height", "min", 0.15, None, 0.30,
     "提膝高度应大于0.15，当前{value}，注意充分提膝", "warning"),
    (exercise_ids["mountain_climber"], "mc_tempo", "节奏稳定性", "tempo_consistency", "min", 0.6, None, 0.25,
     "节奏稳定性应大于0.6，当前{value}，保持匀速", "warning"),
    (exercise_ids["mountain_climber"], "mc_core_stability", "核心稳定", "core_stability", "max", 0.0, 12.0, 0.15,
     "核心偏离应小于12°，当前偏离{value}°", "warning"),
    # 引体向上规则
    (exercise_ids["pull_up"], "pullup_chin_over_bar", "下巴过杆", "chin_height", "min", 0.0, None, 0.35,
     "下巴需过杆，当前高度{value}，注意充分拉起", "error"),
    (exercise_ids["pull_up"], "pullup_elbow_angle_top", "顶部肘部角度", "elbow_angle_top", "max", 0.0, 60.0, 0.25,
     "顶部肘部角度应小于60°，当前{value}°，注意充分拉起", "warning"),
    (exercise_ids["pull_up"], "pullup_descent_speed", "下降速度", "descent_speed", "max", 0.0, 0.5, 0.20,
     "下降速度应控制在0.5以内，当前{value}，注意缓慢下放", "warning"),
    (exercise_ids["pull_up"], "pullup_body_swing", "身体摆动", "body_swing", "max", 0.0, 10.0, 0.20,
     "身体摆动应小于10°，当前{value}°，避免借力", "warning"),
    # 哑铃弯举规则
    (exercise_ids["dumbbell_curl"], "dc_elbow_position", "肘部位置", "elbow_displacement", "max", 0.0, 0.05, 0.35,
     "肘部位移应小于0.05，当前{value}，注意上臂固定", "error"),
    (exercise_ids["dumbbell_curl"], "dc_curl_range", "弯举幅度", "curl_range", "min", 120.0, None, 0.30,
     "弯举幅度应大于120°，当前{value}°，注意充分弯举", "warning"),
    (exercise_ids["dumbbell_curl"], "dc_body_sway", "身体晃动", "body_sway", "max", 0.0, 5.0, 0.20,
     "身体晃动应小于5°，当前{value}°，避免身体借力", "warning"),
    (exercise_ids["dumbbell_curl"], "dc_descent_control", "下放控制", "descent_speed", "max", 0.0, 0.6, 0.15,
     "下放速度应控制在0.6以内，当前{value}，注意缓慢下放", "warning"),
    # 哑铃推举规则
    (exercise_ids["dumbbell_press"], "dp_arm_extension", "手臂伸直度", "arm_extension_angle", "min", 160.0, None, 0.30,
     "推举顶部手臂角度应大于160°，当前{value}°，注意充分伸直", "error"),
    (exercise_ids["dumbbell_press"], "dp_lower_back", "腰部反弓", "lower_back_arch", "max", 0.0, 10.0, 0.25,
     "腰部反弓应小于10°，当前{value}°，注意收紧核心", "error"),
    (exercise_ids["dumbbell_press"], "dp_shoulder_symmetry", "肩部对称性", "shoulder_symmetry_diff", "max", 0.0, 8.0, 0.25,
     "左右肩部高度差应小于8°，当前差{value}°，注意对称发力", "warning"),
    (exercise_ids["dumbbell_press"], "dp_descent_control", "下放控制", "descent_speed", "max", 0.0, 0.5, 0.20,
     "下放速度应控制在0.5以内，当前{value}，注意缓慢下放", "warning"),
    # 高抬腿规则
    (exercise_ids["high_knees"], "hk_knee_height", "膝盖抬起高度", "knee_raise_height", "min", 0.2, None, 0.35,
     "膝盖抬起高度应大于0.2，当前{value}，注意抬至大腿平行", "error"),
    (exercise_ids["high_knees"], "hk_tempo", "节奏稳定性", "tempo_consistency", "min", 0.6, None, 0.30,
     "节奏稳定性应大于0.6，当前{value}，保持匀速", "warning"),
    (exercise_ids["high_knees"], "hk_core_stability", "核心稳定", "core_stability", "max", 0.0, 10.0, 0.20,
     "核心偏离应小于10°，当前偏离{value}°", "warning"),
    (exercise_ids["high_knees"], "hk_posture", "身体姿态", "trunk_angle", "max", 0.0, 10.0, 0.15,
     "身体后仰应小于10°，当前{value}°，保持上身直立", "warning"),
    # 俄罗斯转体规则
    (exercise_ids["russian_twist"], "rt_rotation_range", "转体幅度", "rotation_angle", "min", 30.0, None, 0.35,
     "转体幅度应大于30°，当前{value}°，注意充分旋转", "warning"),
    (exercise_ids["russian_twist"], "rt_back_straight", "背部挺直度", "back_angle", "max", 0.0, 15.0, 0.25,
     "背部弯曲应小于15°，当前{value}°，注意挺直背部", "error"),
    (exercise_ids["russian_twist"], "rt_core_engagement", "核心参与度", "core_engagement", "min", 0.5, None, 0.25,
     "核心参与度应大于0.5，当前{value}，注意核心发力", "warning"),
    (exercise_ids["russian_twist"], "rt_stability", "身体稳定性", "body_sway", "max", 0.0, 8.0, 0.15,
     "身体晃动应小于8°，当前{value}°，保持稳定", "warning"),
    # 臀桥规则
    (exercise_ids["glute_bridge"], "gb_hip_height", "臀部抬起高度", "hip_raise_height", "min", 0.15, None, 0.35,
     "臀部抬起高度应大于0.15，当前{value}，注意充分抬起", "error"),
    (exercise_ids["glute_bridge"], "gb_body_line", "肩髋膝直线度", "body_line_angle", "max", 0.0, 10.0, 0.30,
     "肩-髋-膝偏离直线应小于10°，当前偏离{value}°", "warning"),
    (exercise_ids["glute_bridge"], "gb_lower_back", "腰部代偿", "lower_back_arch", "max", 0.0, 8.0, 0.20,
     "腰部代偿应小于8°，当前{value}°，注意臀部发力", "warning"),
    (exercise_ids["glute_bridge"], "gb_descent_control", "下放控制", "descent_speed", "max", 0.0, 0.5, 0.15,
     "下放速度应控制在0.5以内，当前{value}，注意缓慢下放", "warning"),
]

for ex_id, rule_key, name, metric, operator, t_min, t_max, weight, feedback, severity in rules_data:
    created = now - timedelta(days=20)
    updated = now - timedelta(days=random.randint(1, 5))
    cur.execute(
        "INSERT INTO exercise_rules (exercise_id, rule_key, name, metric, operator, threshold_min, threshold_max, score_weight, feedback_template, severity, is_active, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s,%s)",
        (ex_id, rule_key, name, metric, operator, t_min, t_max, weight, feedback, severity, created, updated)
    )
conn.commit()
cur.execute("SELECT COUNT(*) FROM exercise_rules")
rules_count = cur.fetchone()[0]
print(f"   插入 {rules_count} 条评估规则")

# ============================================================
# 5. sessions — 训练记录（模拟真实训练场景）
# ============================================================
print("\n5. 插入训练记录数据...")

# 真实训练场景模拟
exercise_keys = ["squat", "push_up", "jumping_jack", "plank", "lunge", "high_knees", "mountain_climber", "burpee"]
student_users = [("zhangminghao", user_ids["zhangminghao"]),
                 ("liwenbo", user_ids["liwenbo"]),
                 ("wangjiaqi", user_ids["wangjiaqi"]),
                 ("chenyuhan", user_ids["chenyuhan"])]

session_records = []
session_id_counter = 1

for student_name, student_id in student_users:
    # 每个学生 5-8 条训练记录，分布在过去 20 天
    num_sessions = random.randint(5, 8)
    for i in range(num_sessions):
        exercise = random.choice(exercise_keys)
        days_ago = random.randint(1, 20)
        session_time = now - timedelta(days=days_ago, hours=random.randint(8, 22))

        # 根据动作类型生成合理的训练数据
        if exercise == "plank":
            duration = random.randint(30, 120)  # 平板支撑时间较短
            total_count = 1
            valid_count = 1
            error_count = random.randint(0, 3)
            avg_score = round(random.uniform(60, 95), 1)
        elif exercise in ("jumping_jack", "high_knees", "mountain_climber"):
            duration = random.randint(60, 300)  # 心肺训练中等时长
            total_count = random.randint(20, 60)
            valid_count = max(1, total_count - random.randint(2, 10))
            error_count = total_count - valid_count
            avg_score = round(random.uniform(65, 92), 1)
        elif exercise == "burpee":
            duration = random.randint(120, 360)
            total_count = random.randint(8, 20)
            valid_count = max(1, total_count - random.randint(1, 5))
            error_count = total_count - valid_count
            avg_score = round(random.uniform(55, 85), 1)
        else:
            duration = random.randint(180, 600)  # 力量训练较长
            total_count = random.randint(10, 30)
            valid_count = max(1, total_count - random.randint(1, 8))
            error_count = total_count - valid_count
            avg_score = round(random.uniform(60, 95), 1)

        session_uuid = f"sess_{session_id_counter:04d}_{student_name}_{exercise}"
        cur.execute(
            "INSERT INTO sessions (session_id, user_id, exercise, duration_seconds, total_count, valid_count, error_count, average_score, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (session_uuid, student_id, exercise, duration, total_count, valid_count, error_count, avg_score, session_time)
        )

        # 获取自增 ID
        cur.execute("SELECT LAST_INSERT_ID()")
        db_id = cur.fetchone()[0]
        session_records.append({
            "id": db_id,
            "session_id": session_uuid,
            "user_id": student_id,
            "user_name": student_name,
            "exercise": exercise,
            "avg_score": avg_score,
            "error_count": error_count,
            "total_count": total_count,
            "duration": duration,
            "created_at": session_time
        })
        session_id_counter += 1

conn.commit()
cur.execute("SELECT COUNT(*) FROM sessions")
sessions_count = cur.fetchone()[0]
print(f"   插入 {sessions_count} 条训练记录")
for sr in session_records[:5]:
    print(f"     {sr['user_name']} - {sr['exercise']} - 得分:{sr['avg_score']} - {sr['created_at'].strftime('%Y-%m-%d')}")

# ============================================================
# 6. analysis_events — 分析事件（具体的错误帧记录）
# ============================================================
print("\n6. 插入分析事件数据...")

# 为每条训练记录生成 3-8 个分析事件
event_types = {
    "squat": [
        ("knee_angle_too_small", "error", "深蹲底部膝盖角度不足", "下蹲时膝盖角度仅为{value}°，建议下蹲至90°左右"),
        ("knee_valgus", "error", "膝盖内扣", "检测到膝盖内扣，角度偏差{value}°，注意膝盖与脚尖方向一致"),
        ("back_rounded", "warning", "背部弯曲", "背部弯曲角度{value}°，保持背部挺直"),
        ("depth_insufficient", "warning", "下蹲深度不足", "下蹲深度不够，髋部角度{value}°，建议继续下蹲"),
        ("trunk_lean_excessive", "warning", "躯干过度前倾", "躯干前倾{value}°，减少前倾保持上身直立"),
    ],
    "push_up": [
        ("elbow_angle_insufficient", "error", "肘部角度不足", "下降时肘部角度{value}°，建议下降至90°以下"),
        ("body_sag", "error", "身体塌腰", "检测到腰部下沉{value}°，收紧核心保持身体直线"),
        ("incomplete_range", "warning", "动作幅度不足", "未完成完整动作幅度，当前幅度{value}°"),
        ("asymmetry", "warning", "左右不对称", "左右肘部角度差{value}°，注意对称发力"),
    ],
    "jumping_jack": [
        ("arm_not_fully_raised", "warning", "手臂未完全抬起", "手臂抬起高度不足，当前{value}，建议举过头顶"),
        ("leg_spread_insufficient", "warning", "腿部张开不足", "腿部张开角度{value}°，建议大于30°"),
        ("async_movement", "warning", "手脚不同步", "手脚动作时间差{value}s，注意协调配合"),
    ],
    "plank": [
        ("hip_sag", "error", "髋部下沉", "髋部下沉{value}°，收紧核心抬起髋部"),
        ("hip_raise", "warning", "臀部翘起", "臀部抬高{value}°，降低臀部保持平直"),
        ("shoulder_elbow_misalign", "warning", "肩肘未对齐", "肩肘水平偏移{value}，调整肘部位置"),
        ("body_shake", "info", "身体抖动", "检测到身体抖动，注意核心稳定"),
    ],
    "lunge": [
        ("knee_over_toe", "error", "膝盖超过脚尖", "前膝超过脚尖{value}cm，增大跨步距离"),
        ("trunk_lean", "warning", "身体前倾", "躯干前倾{value}°，保持上身直立"),
        ("back_knee_straight", "warning", "后腿未弯曲", "后膝角度{value}°，注意后腿弯曲下蹲"),
    ],
    "high_knees": [
        ("knee_not_high_enough", "error", "膝盖抬起高度不足", "膝盖高度{value}，需抬至大腿平行地面"),
        ("tempo_unstable", "warning", "节奏不稳", "节奏波动{value}，保持匀速"),
        ("body_lean_back", "warning", "身体后仰", "身体后仰{value}°，保持上身直立"),
    ],
    "mountain_climber": [
        ("hip_too_high", "error", "臀部抬高", "臀部抬高{value}，降低臀部保持平直"),
        ("knee_not_high", "warning", "提膝不足", "提膝高度{value}，注意向胸部靠拢"),
        ("tempo_unstable", "warning", "节奏不稳", "节奏波动{value}，保持匀速"),
    ],
    "burpee": [
        ("pushup_not_deep", "warning", "俯卧撑不到位", "俯卧撑肘部角度{value}°，建议下降至90°"),
        ("jump_not_high", "warning", "跳跃高度不足", "跳跃高度{value}，注意充分跳起"),
        ("core_unstable", "warning", "核心不稳", "核心偏离{value}°，收紧核心"),
    ],
}

total_events = 0
for sr in session_records:
    # 每条训练记录 3-8 个事件
    num_events = random.randint(3, min(8, sr["error_count"] + 3))
    ex_events = event_types.get(sr["exercise"], [])

    for i in range(num_events):
        if not ex_events:
            break
        event_type, severity, _, message_template = random.choice(ex_events)

        # 生成具体的数值
        value = round(random.uniform(5, 45), 1)
        message = message_template.replace("{value}", str(value))

        frame_index = random.randint(0, max(1, sr["duration"] // 30))
        timestamp = round(random.uniform(0, max(1, sr["duration"])), 2)
        score_delta = round(random.uniform(-5, -1) if severity == "error" else random.uniform(-3, -0.5), 2)

        # 简单的 keypoints JSON
        keypoints = json.dumps({
            "frame": frame_index,
            "timestamp": timestamp,
            "key_points": {
                "left_knee": [random.uniform(0.3, 0.7), random.uniform(0.4, 0.8), 0.9],
                "right_knee": [random.uniform(0.3, 0.7), random.uniform(0.4, 0.8), 0.9],
            }
        })

        event_time = sr["created_at"] + timedelta(seconds=timestamp)
        cur.execute(
            "INSERT INTO analysis_events (session_id, rule_id, event_type, severity, frame_index, timestamp_seconds, score_delta, message, keypoints_json, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (sr["id"], None, event_type, severity, frame_index, timestamp, score_delta, message, keypoints, event_time)
        )
        total_events += 1

conn.commit()
print(f"   插入 {total_events} 条分析事件")

# ============================================================
# 7. reports — 训练报告
# ============================================================
print("\n7. 插入训练报告数据...")

# 为部分训练记录生成报告 (约 60% 的记录有报告)
report_count = 0
for sr in session_records:
    if random.random() > 0.6:
        continue

    report_uuid = f"rpt_{sr['session_id']}"
    title = f"{sr['user_name']}的{sr['exercise']}训练报告"
    report_type = "session_summary"
    fmt = "json"
    status = "completed"
    file_uri = f"/storage/reports/{report_uuid}.json"

    # 汇总 JSON
    summary = json.dumps({
        "exercise": sr["exercise"],
        "total_count": sr["total_count"],
        "valid_count": max(0, sr["total_count"] - sr["error_count"]),
        "error_count": sr["error_count"],
        "average_score": sr["avg_score"],
        "duration_seconds": sr["duration"],
        "main_issues": [e[2] for e in event_types.get(sr["exercise"], [])[:3]],
        "suggestions": [
            "注意保持正确的动作姿势",
            "加强核心力量训练",
            "控制动作节奏，避免过快",
        ],
        "improvement": "相比上次训练，动作质量有所提升，建议继续保持。",
    }, ensure_ascii=False)

    generated_at = sr["created_at"] + timedelta(minutes=5)
    cur.execute(
        "INSERT INTO reports (report_id, user_id, session_id, title, report_type, format, file_uri, status, summary_json, generated_at, created_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (report_uuid, sr["user_id"], sr["id"], title, report_type, fmt, file_uri, status, summary, generated_at, generated_at)
    )
    report_count += 1

conn.commit()
print(f"   插入 {report_count} 条训练报告")

# ============================================================
# 8. analysis_tasks — 分析任务
# ============================================================
print("\n8. 插入分析任务数据...")

task_statuses = ["completed", "completed", "completed", "completed", "pending", "failed"]
task_count = 0

for sr in session_records[:15]:  # 前15条记录有对应的分析任务
    task_uuid = f"task_{sr['session_id']}"
    status = random.choice(task_statuses)
    source_uri = f"/storage/uploads/{sr['session_id']}.mp4"
    output_uri = f"/storage/outputs/{sr['session_id']}.json" if status == "completed" else None
    error_msg = None
    if status == "failed":
        error_msg = "视频处理超时，请重试"
    elif status == "pending":
        error_msg = None

    created = sr["created_at"] - timedelta(seconds=5)
    updated = created + timedelta(minutes=2) if status == "completed" else created + timedelta(seconds=30)

    cur.execute(
        "INSERT INTO analysis_tasks (task_id, exercise, source_uri, status, output_uri, error_message, created_at, updated_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (task_uuid, sr["exercise"], source_uri, status, output_uri, error_msg, created, updated)
    )
    task_count += 1

conn.commit()
print(f"   插入 {task_count} 条分析任务")

# ============================================================
# 同步自增 ID
# ============================================================
cur.execute("ALTER TABLE users AUTO_INCREMENT = %s", (len(real_users) + 1,))
cur.execute("ALTER TABLE exercises AUTO_INCREMENT = %s", (len(exercises_data) + 1,))
cur.execute("ALTER TABLE exercise_rules AUTO_INCREMENT = %s", (rules_count + 1,))
cur.execute("ALTER TABLE sessions AUTO_INCREMENT = %s", (sessions_count + 1,))
cur.execute("ALTER TABLE analysis_events AUTO_INCREMENT = %s", (total_events + 1,))
cur.execute("ALTER TABLE reports AUTO_INCREMENT = %s", (report_count + 1,))
cur.execute("ALTER TABLE analysis_tasks AUTO_INCREMENT = %s", (task_count + 1,))
conn.commit()

# ============================================================
# 最终验证
# ============================================================
print("\n" + "=" * 50)
print("数据填充完成！最终统计：")
print("=" * 50)
for table in ['users', 'exercises', 'exercise_rules', 'sessions', 'analysis_events', 'reports', 'analysis_tasks']:
    cur.execute(f"SELECT COUNT(*) FROM `{table}`")
    count = cur.fetchone()[0]
    print(f"  {table}: {count} 条")

cur.close()
conn.close()
print("\nDone!")
