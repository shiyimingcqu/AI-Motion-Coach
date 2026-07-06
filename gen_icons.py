import os, math
from PIL import Image, ImageDraw

SIZE = 81
OUT = r"D:\02-学习\项目实训\运动姿态评估与纠错系统\miniprogram\assets\icons"

NORMAL = (154, 161, 179, 255)     # #9aa1b3
ACTIVE = (79, 140, 255, 255)       # #4f8cff

def make_icon(color, draw_fn):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    draw_fn(d, color)
    return img

def save(img, name):
    path = os.path.join(OUT, name)
    img.save(path, "PNG")
    return os.path.getsize(path)

# ─── 首页 - 房子 ───
def draw_home(d, color):
    # 屋顶
    d.polygon([(40, 12), (4, 40), (76, 40)], fill=color)
    # 房身
    d.rectangle([12, 40, 68, 68], fill=color)
    # 门洞（镂空透明）
    d.rectangle([30, 48, 50, 68], fill=(0,0,0,0))

# ─── 评估 - 闪电 ───
def draw_assess(d, color):
    d.polygon([
        (42, 8), (24, 40), (36, 40), (26, 72),
        (54, 36), (42, 36), (52, 8)
    ], fill=color)

# ─── 记录 - 文档/列表 ───
def draw_records(d, color):
    # clipboard body
    d.rounded_rectangle([10, 24, 70, 72], 12, fill=color)
    # top clip
    d.rounded_rectangle([20, 6, 60, 30], 8, fill=color)
    # 3 lines
    lc = (255, 255, 255, 255)
    for yy in [36, 48, 60]:
        d.rounded_rectangle([20, yy, 60, yy+4], 2, fill=lc)

# ─── 我的 - 人物 ───
def draw_profile(d, color):
    # head
    d.ellipse([28, 10, 52, 36], fill=color)
    # body
    d.ellipse([14, 40, 66, 76], fill=color)

icons_map = {
    "home.png":          (NORMAL, draw_home),
    "home-active.png":   (ACTIVE, draw_home),
    "exercise.png":      (NORMAL, draw_assess),
    "exercise-active.png": (ACTIVE, draw_assess),
    "report.png":        (NORMAL, draw_records),
    "report-active.png": (ACTIVE, draw_records),
    "profile.png":       (NORMAL, draw_profile),
    "profile-active.png": (ACTIVE, draw_profile),
}

for name, (color, fn) in icons_map.items():
    img = make_icon(color, fn)
    size = save(img, name)
    print(f"  {name:24s} {size:5d} bytes")

print("\n8 个 tabBar 图标生成完毕！")
print(f"普通态: #{NORMAL[0]:02x}{NORMAL[1]:02x}{NORMAL[2]:02x}  激活态: #{ACTIVE[0]:02x}{ACTIVE[1]:02x}{ACTIVE[2]:02x}")
