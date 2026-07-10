from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, ImageFilter


ROOT = Path(r"D:\02-学习\项目实训\4")
OUT_DIR = ROOT / "deliverables" / "generated_slide_images"
BG_DIR = Path(r"C:\Users\14580\.codex\generated_images\019f457f-4c59-7412-98d0-834e67a8571e")

BG_PATHS = [
    BG_DIR / "ig_0723712cf8dd1633016a4f6a3f5764819683733037ec8ac8a1.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6a7c8c7c8196a492c548d5be3864.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6ab72b58819693b9e6f762fd97a7.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6aebce9c8196a779a2b2b368fc2f.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6b213e6881968b04d31f7b5978ed.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6b5c746081969e06ab0e0a58ee84.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6b9b1f8c8196ae28f15dca3cecb3.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6bd2a5ec8196a6a408338a898887.png",
    BG_DIR / "ig_0723712cf8dd1633016a4f6c1198348196a4bc77e2cf66b67b.png",
]

W, H = 1920, 1080
FONT = Path(r"C:\Windows\Fonts\msyh.ttc")
FONT_BOLD = Path(r"C:\Windows\Fonts\msyhbd.ttc")

INK = (12, 30, 66)
MUTED = (83, 101, 138)
BLUE = (72, 118, 255)
VIOLET = (112, 76, 255)
GREEN = (63, 201, 136)
ORANGE = (255, 147, 55)
RED = (255, 84, 78)


def font(size, bold=False):
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT), size=size)


def crop_16x9(img):
    img = img.convert("RGB")
    iw, ih = img.size
    target = 16 / 9
    if iw / ih > target:
        nw = int(ih * target)
        left = (iw - nw) // 2
        img = img.crop((left, 0, left + nw, ih))
    else:
        nh = int(iw / target)
        top = (ih - nh) // 2
        img = img.crop((0, top, iw, top + nh))
    return img.resize((W, H), Image.Resampling.LANCZOS)


def overlay_wash(img, alpha=82):
    layer = Image.new("RGBA", (W, H), (248, 252, 255, alpha))
    return Image.alpha_composite(img.convert("RGBA"), layer)


def rounded(draw, box, radius=34, fill=(255, 255, 255, 220), outline=(219, 229, 255, 230), width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def shadowed_card(base, box, radius=32, fill=(255, 255, 255, 226), outline=(220, 230, 255, 230)):
    x1, y1, x2, y2 = box
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x1 + 8, y1 + 12, x2 + 8, y2 + 12), radius=radius, fill=(80, 108, 170, 28))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    base.alpha_composite(shadow)
    d = ImageDraw.Draw(base)
    rounded(d, box, radius=radius, fill=fill, outline=outline)
    return d


def pill(draw, x, y, text, color=VIOLET, bg=(246, 241, 255, 238), fs=30, pad_x=24):
    f = font(fs, True)
    bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle((x, y, x + tw + pad_x * 2, y + th + 22), radius=28, fill=bg)
    draw.text((x + pad_x, y + 8), text, font=f, fill=color)
    return x + tw + pad_x * 2


def title(draw, main, sub=None):
    draw.text((92, 72), main, font=font(66, True), fill=INK)
    if sub:
        draw.text((96, 158), sub, font=font(30), fill=MUTED)


def wrap_text(draw, text, fnt, max_width):
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def multiline(draw, xy, text, fnt, fill=MUTED, max_width=520, line_gap=10):
    x, y = xy
    for line in wrap_text(draw, text, fnt, max_width):
        draw.text((x, y), line, font=fnt, fill=fill)
        y += fnt.size + line_gap
    return y


def draw_cards(draw, items, x, y, w, h, gap, cols, accent=BLUE):
    for idx, item in enumerate(items):
        cx = x + (idx % cols) * (w + gap)
        cy = y + (idx // cols) * (h + gap)
        rounded(draw, (cx, cy, cx + w, cy + h), radius=30, fill=(255, 255, 255, 232))
        draw.ellipse((cx + 30, cy + 34, cx + 86, cy + 90), fill=(238, 244, 255))
        draw.ellipse((cx + 45, cy + 49, cx + 71, cy + 75), fill=accent)
        if isinstance(item, tuple):
            head, body = item
        else:
            head, body = item, ""
        draw.text((cx + 112, cy + 34), head, font=font(31, True), fill=INK)
        if body:
            multiline(draw, (cx + 112, cy + 84), body, font(23), fill=MUTED, max_width=w - 140, line_gap=7)


def slide_1(img):
    img = overlay_wash(img, 68)
    d = ImageDraw.Draw(img)
    title(d, "姿态棱镜", "AI 运动姿态评估与纠错系统")
    d.text((96, 238), "让每一次训练都能被看见、被分析、被改进", font=font(40, True), fill=VIOLET)
    pill(d, 96, 318, "课程项目汇报", BLUE, (232, 241, 255, 235), fs=28)
    x = pill(d, 96, 390, "3D 回放", VIOLET, fs=27)
    pill(d, x + 16, 390, "标准动作对比", GREEN, (230, 251, 242, 235), fs=27)
    return img


def slide_2(img):
    img = overlay_wash(img, 80)
    d = ImageDraw.Draw(img)
    title(d, "目录", "从团队、背景、架构到功能创新与未来规划")
    items = [
        ("团队成员介绍", "项目分工与协作"),
        ("项目背景", "为什么需要姿态棱镜"),
        ("技术架构解析", "从采集到可视化"),
        ("项目功能与创新点", "核心能力与亮点"),
        ("未来发展展望", "后续迭代方向"),
    ]
    draw_cards(d, items, 140, 270, 520, 170, 46, 2, VIOLET)
    return img


def slide_3(img):
    img = overlay_wash(img, 88)
    d = ImageDraw.Draw(img)
    title(d, "团队成员介绍", "围绕产品、算法、接口与多端体验协同完成")
    roles = ["项目统筹", "前端与交互", "后端与接口", "姿态算法", "小程序端"]
    for i, role in enumerate(roles):
        x = 118 + i * 350
        shadowed_card(img, (x, 300, x + 290, 760), radius=34)
        d = ImageDraw.Draw(img)
        d.ellipse((x + 82, 345, x + 208, 471), fill=(232, 241, 255))
        d.ellipse((x + 121, 382, x + 169, 430), fill=(106, 87, 255))
        d.rounded_rectangle((x + 68, 510, x + 222, 550), radius=20, fill=(246, 241, 255))
        d.text((x + 58, 595), role, font=font(34, True), fill=INK)
        d.text((x + 67, 654), "职责标签", font=font(24), fill=MUTED)
    return img


def slide_4(img):
    img = overlay_wash(img, 86)
    d = ImageDraw.Draw(img)
    title(d, "运动热潮下的新问题", "痛点不是不想动，而是不知道动作是否标准")
    stats = [("18 亿", "成年人身体活动不足"), ("80%+", "青少年身体活动不足"), ("5.5 亿", "中国体育健身人群规模")]
    for i, (num, label) in enumerate(stats):
        x = 100 + i * 575
        shadowed_card(img, (x, 270, x + 500, 500), radius=36)
        d = ImageDraw.Draw(img)
        d.text((x + 44, 310), num, font=font(70, True), fill=[BLUE, VIOLET, GREEN][i])
        multiline(d, (x + 48, 408), label, font(29, True), fill=INK, max_width=395)
    shadowed_card(img, (126, 650, 1070, 875), radius=38, fill=(255, 255, 255, 236))
    d = ImageDraw.Draw(img)
    d.text((180, 700), "常见困惑", font=font(38, True), fill=INK)
    multiline(d, (180, 760), "自己练的时候很难判断动作幅度、节奏和姿态是否正确。", font(31), fill=MUTED, max_width=780, line_gap=12)
    return img


def slide_5(img):
    img = overlay_wash(img, 72)
    d = ImageDraw.Draw(img)
    title(d, "真实场景视频", "用 Web 端 3D 回放复盘训练过程")
    shadowed_card(img, (110, 230, 1240, 875), radius=40, fill=(255, 255, 255, 232))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((150, 285, 1200, 745), radius=32, fill=(20, 34, 72, 210))
    d.polygon([(650, 480), (650, 585), (745, 532)], fill=(255, 255, 255, 235))
    d.rounded_rectangle((220, 790, 1130, 814), radius=12, fill=(224, 234, 255))
    d.rounded_rectangle((220, 790, 610, 814), radius=12, fill=(112, 76, 255))
    d.text((150, 810), "男生使用 3D 回放复盘训练", font=font(30, True), fill=INK)
    items = [("不请教练，也能看懂动作", ""), ("查看单次动作", ""), ("和标准动作同屏对比", "")]
    draw_cards(d, items, 1310, 282, 500, 150, 38, 1, VIOLET)
    return img


def slide_6(img):
    img = overlay_wash(img, 82)
    d = ImageDraw.Draw(img)
    title(d, "项目定位", "每个人都能使用的 AI 运动教练")
    items = [
        ("看得见动作", "用 3D 方式还原训练过程"),
        ("看得懂问题", "把动作异常转成易懂提示"),
        ("看得到进步", "保留训练记录与结果"),
        ("能复盘动作", "支持完整训练和单次动作回放"),
    ]
    draw_cards(d, items, 120, 272, 805, 168, 40, 2, BLUE)
    scenarios = ["居家健身", "体育教学", "康复辅助", "健身房自助训练"]
    x = 190
    for s in scenarios:
        x = pill(d, x, 810, s, VIOLET, (246, 241, 255, 238), fs=28, pad_x=30) + 30
    return img


def slide_7(img):
    img = overlay_wash(img, 88)
    d = ImageDraw.Draw(img)
    title(d, "技术架构解析", "从采集、识别、分析到 Web 可视化的完整链路")
    steps = ["小程序 / 摄像头采集", "姿态关键点识别", "后端动作分析", "Web 可视化"]
    for i, step in enumerate(steps):
        x = 105 + i * 445
        shadowed_card(img, (x, 395, x + 345, 635), radius=36)
        d = ImageDraw.Draw(img)
        d.ellipse((x + 127, 435, x + 217, 525), fill=(232, 241, 255))
        d.ellipse((x + 153, 461, x + 191, 499), fill=[BLUE, GREEN, ORANGE, VIOLET][i])
        multiline(d, (x + 42, 555), step, font(31, True), fill=INK, max_width=270, line_gap=8)
        if i < 3:
            ax = x + 360
            d.line((ax, 515, ax + 72, 515), fill=(115, 144, 230), width=6)
            d.polygon([(ax + 72, 515), (ax + 48, 500), (ax + 48, 530)], fill=(115, 144, 230))
    return img


def slide_8(img):
    img = overlay_wash(img, 88)
    d = ImageDraw.Draw(img)
    title(d, "核心技术模块", "每一层都服务于采集、分析和展示体验")
    modules = [
        ("Vue 3 + Vite", "前端页面与交互"),
        ("FastAPI", "后端接口"),
        ("MediaPipe", "姿态关键点"),
        ("Three.js", "3D 可视化"),
        ("小程序端", "移动采集入口"),
        ("SQLite / Storage", "训练数据存储"),
    ]
    draw_cards(d, modules, 120, 260, 520, 180, 38, 3, VIOLET)
    return img


def slide_9(img):
    img = overlay_wash(img, 82)
    d = ImageDraw.Draw(img)
    title(d, "功能一：训练采集与动作识别", "不用穿戴设备，只需要摄像头或小程序采集")
    steps = [
        ("采集", "摄像头记录训练动作"),
        ("分析", "识别人体关键点与动作次数"),
        ("展示", "保存骨架数据并生成结果"),
    ]
    for i, (head, body) in enumerate(steps):
        x = 150 + i * 565
        shadowed_card(img, (x, 320, x + 460, 705), radius=40)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x + 55, 370, x + 170, 485), radius=28, fill=(232, 241, 255))
        d.ellipse((x + 92, 407, x + 132, 447), fill=[BLUE, VIOLET, GREEN][i])
        d.text((x + 55, 535), head, font=font(45, True), fill=INK)
        multiline(d, (x + 55, 602), body, font(29), fill=MUTED, max_width=350, line_gap=10)
        if i < 2:
            ax = x + 485
            d.line((ax, 510, ax + 55, 510), fill=(116, 144, 230), width=6)
            d.polygon([(ax + 55, 510), (ax + 34, 496), (ax + 34, 524)], fill=(116, 144, 230))
    pill(d, 615, 810, "自动计数", BLUE, (232, 241, 255, 238), fs=30)
    pill(d, 850, 810, "保存骨架数据", GREEN, (231, 250, 241, 238), fs=30)
    return img


SLIDE_FUNCS = [slide_1, slide_2, slide_3, slide_4, slide_5, slide_6, slide_7, slide_8, slide_9]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT_DIR / "raw_backgrounds"
    raw_dir.mkdir(exist_ok=True)

    final_paths = []
    for i, (bg, func) in enumerate(zip(BG_PATHS, SLIDE_FUNCS), 1):
        raw_copy = raw_dir / f"slide_{i:02d}_background.png"
        shutil.copy2(bg, raw_copy)
        img = crop_16x9(Image.open(bg))
        img = func(img)
        out = OUT_DIR / f"slide_{i:02d}.png"
        img.convert("RGB").save(out, quality=96)
        final_paths.append(out)

    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 3, thumb_h * 3), "white")
    for idx, path in enumerate(final_paths):
        im = Image.open(path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(im, ((idx % 3) * thumb_w, (idx // 3) * thumb_h))
    sheet.save(OUT_DIR / "contact_sheet.jpg", quality=92)
    print("\n".join(str(p) for p in final_paths))
    print(OUT_DIR / "contact_sheet.jpg")


if __name__ == "__main__":
    main()
