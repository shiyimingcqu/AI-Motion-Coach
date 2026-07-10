from pathlib import Path
import shutil

from PIL import Image, ImageDraw

from compose_generated_slide_images import (
    W,
    H,
    BLUE,
    GREEN,
    INK,
    MUTED,
    ORANGE,
    RED,
    VIOLET,
    crop_16x9,
    draw_cards,
    font,
    multiline,
    overlay_wash,
    pill,
    shadowed_card,
    title,
)


ROOT = Path(r"D:\02-学习\项目实训\4")
OUT_DIR = ROOT / "deliverables" / "generated_slide_images"
BG_DIR = Path(r"C:\Users\14580\.codex\generated_images\019f457f-4c59-7412-98d0-834e67a8571e")

BG_PATHS = [
    BG_DIR / "ig_0bf9551539eb38c0016a4f6d952db88191ae7baac396c56ada.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6de377708191b935352cb059c355.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6e2876f8819192a368236b39a1e3.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6e6d4bb481919e998f7c4b1148d1.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6eb2f5cc8191b69b184c9fba1df2.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6efaed308191b584e27e2e32f331.png",
    BG_DIR / "ig_0bf9551539eb38c0016a4f6f3db7c0819191a67917bd9312db.png",
]


def slide_10(img):
    img = overlay_wash(img, 70)
    d = ImageDraw.Draw(img)
    title(d, "功能二：Web 端 3D 动作回放", "完整训练、单次动作与播放控制集中在一个界面")
    shadowed_card(img, (110, 232, 1248, 842), radius=42, fill=(255, 255, 255, 222))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((165, 298, 1188, 662), radius=34, fill=(17, 31, 70, 210))
    d.text((220, 356), "3D 骨架回放", font=font(44, True), fill=(255, 255, 255))
    d.line((285, 520, 495, 400), fill=(113, 185, 255), width=8)
    d.line((495, 400, 685, 520), fill=(116, 240, 174), width=8)
    d.line((495, 400, 505, 285), fill=(255, 255, 255), width=7)
    d.ellipse((475, 258, 535, 318), fill=(255, 255, 255))
    d.rounded_rectangle((230, 724, 1080, 750), radius=13, fill=(222, 232, 255))
    d.rounded_rectangle((230, 724, 615, 750), radius=13, fill=VIOLET)
    pill(d, 250, 775, "播放", VIOLET, fs=26)
    pill(d, 390, 775, "暂停", BLUE, (232, 241, 255, 238), fs=26)
    pill(d, 530, 775, "调速", GREEN, (231, 250, 241, 238), fs=26)
    cards = [
        ("完整训练", "查看整段运动过程"),
        ("单次动作", "第 1 次、第 2 次快速切换"),
        ("播放控制", "进度条、速度与暂停"),
    ]
    draw_cards(d, cards, 1320, 300, 475, 148, 34, 1, VIOLET)
    return img


def slide_11(img):
    img = overlay_wash(img, 72)
    d = ImageDraw.Draw(img)
    title(d, "功能三：标准动作 3D 对比", "把我的动作和标准动作放在同一屏里看差异")
    shadowed_card(img, (90, 260, 900, 790), radius=40, fill=(255, 255, 255, 224))
    shadowed_card(img, (1020, 260, 1830, 790), radius=40, fill=(255, 255, 255, 224))
    d = ImageDraw.Draw(img)
    d.text((142, 305), "我的动作", font=font(42, True), fill=BLUE)
    d.text((1072, 305), "标准动作", font=font(42, True), fill=GREEN)
    for ox, color in [(495, BLUE), (1425, GREEN)]:
        d.line((ox, 425, ox - 120, 585), fill=color, width=9)
        d.line((ox, 425, ox + 135, 575), fill=color, width=9)
        d.line((ox, 425, ox, 350), fill=(255, 255, 255), width=7)
        d.ellipse((ox - 28, 322, ox + 28, 378), fill=(255, 255, 255))
        d.line((ox - 120, 585, ox - 170, 705), fill=color, width=9)
        d.line((ox + 135, 575, ox + 205, 698), fill=color, width=9)
    d.line((945, 360, 945, 760), fill=(206, 218, 252), width=4)
    pill(d, 758, 482, "角度差异", ORANGE, (255, 244, 225, 238), fs=28)
    pill(d, 730, 825, "单次动作切换", VIOLET, fs=28)
    pill(d, 1018, 825, "课堂演示", BLUE, (232, 241, 255, 238), fs=28)
    pill(d, 1228, 825, "训练复盘", GREEN, (231, 250, 241, 238), fs=28)
    return img


def slide_12(img):
    img = overlay_wash(img, 82)
    d = ImageDraw.Draw(img)
    title(d, "功能四：真实纠错与训练记录", "只展示后端真实返回的问题，有问题和无问题分开展示")
    shadowed_card(img, (104, 255, 850, 845), radius=42)
    shadowed_card(img, (930, 255, 1815, 845), radius=42)
    d = ImageDraw.Draw(img)
    d.text((160, 310), "单次动作回放", font=font(42, True), fill=INK)
    d.rounded_rectangle((165, 382, 790, 635), radius=30, fill=(20, 35, 75, 210))
    d.text((220, 470), "3D 回放卡片", font=font(38, True), fill=(255, 255, 255))
    d.rounded_rectangle((190, 700, 740, 724), radius=12, fill=(223, 233, 255))
    d.rounded_rectangle((190, 700, 505, 724), radius=12, fill=VIOLET)
    d.text((990, 310), "纠错建议", font=font(42, True), fill=INK)
    issue_cards = [
        (990, 390, "需调整", "后端返回真实问题时显示", RED),
        (990, 555, "正常", "没有问题时显示正常状态", GREEN),
        (990, 720, "训练记录", "按次数保存，方便复盘", BLUE),
    ]
    for x, y, head, body, color in issue_cards:
        d.rounded_rectangle((x, y, 1748, y + 118), radius=28, fill=(255, 255, 255, 238), outline=(219, 229, 255), width=2)
        d.ellipse((x + 30, y + 30, x + 88, y + 88), fill=color)
        d.text((x + 118, y + 25), head, font=font(32, True), fill=INK)
        d.text((x + 118, y + 70), body, font=font(25), fill=MUTED)
    return img


def slide_13(img):
    img = overlay_wash(img, 88)
    d = ImageDraw.Draw(img)
    title(d, "项目功能与创新点", "围绕真实训练过程，让普通用户也能看懂动作")
    items = [
        ("无需穿戴设备", "摄像头或小程序即可采集"),
        ("3D 回放复盘", "训练动作可回看"),
        ("标准动作对比", "差异更直观"),
        ("多端联动", "小程序采集，Web 展示"),
        ("真实数据驱动", "纠错来自后端结果"),
        ("大众友好", "提示更接近日常表达"),
    ]
    draw_cards(d, items, 120, 250, 520, 188, 38, 3, VIOLET)
    return img


def slide_14(img):
    img = overlay_wash(img, 86)
    d = ImageDraw.Draw(img)
    title(d, "项目价值", "让专业指导更普惠")
    values = [
        ("普通用户", "低成本了解动作是否标准"),
        ("体育老师", "辅助课堂动作演示与复盘"),
        ("健身教练", "提升训练反馈效率"),
        ("平台方", "沉淀训练数据与服务能力"),
    ]
    draw_cards(d, values, 130, 310, 790, 190, 48, 2, BLUE)
    shadowed_card(img, (530, 810, 1390, 902), radius=36, fill=(246, 241, 255, 235))
    d = ImageDraw.Draw(img)
    d.text((615, 832), "让更多人以更低成本获得科学、安全的运动指导", font=font(33, True), fill=VIOLET)
    return img


def slide_15(img):
    img = overlay_wash(img, 88)
    d = ImageDraw.Draw(img)
    title(d, "未来发展展望", "从动作扩展到个性化训练，再走向更多真实场景")
    cols = [
        ("近期", ["支持更多动作", "完善纠错文案", "优化 3D 对比"]),
        ("中期", ["训练报告自动生成", "个性化训练计划", "接入更多健康数据"]),
        ("长期", ["学校体育与健身房场景", "AI 私教式陪伴", "多人训练数据管理"]),
    ]
    for i, (head, lines) in enumerate(cols):
        x = 110 + i * 600
        shadowed_card(img, (x, 270, x + 520, 745), radius=42)
        d = ImageDraw.Draw(img)
        d.text((x + 52, 320), head, font=font(48, True), fill=[BLUE, VIOLET, GREEN][i])
        y = 410
        for line in lines:
            d.ellipse((x + 58, y + 10, x + 76, y + 28), fill=[BLUE, VIOLET, GREEN][i])
            d.text((x + 96, y), line, font=font(30, True), fill=INK)
            y += 78
    shadowed_card(img, (235, 815, 1688, 930), radius=38, fill=(255, 255, 255, 236))
    d = ImageDraw.Draw(img)
    d.text((310, 848), "目标：让每个人都能用更低成本获得更科学、更安全的运动指导", font=font(34, True), fill=VIOLET)
    return img


def slide_16(img):
    img = overlay_wash(img, 60)
    d = ImageDraw.Draw(img)
    shadowed_card(img, (120, 240, 1040, 625), radius=48, fill=(255, 255, 255, 226))
    d = ImageDraw.Draw(img)
    d.text((190, 320), "谢谢观看", font=font(88, True), fill=INK)
    multiline(
        d,
        (196, 455),
        "姿态棱镜：让运动更科学，让每个人都能安全地练起来",
        font(38, True),
        fill=VIOLET,
        max_width=760,
        line_gap=16,
    )
    pill(d, 190, 705, "课程项目汇报", BLUE, (232, 241, 255, 238), fs=30)
    pill(d, 440, 705, "AI 运动姿态评估与纠错系统", VIOLET, fs=30)
    return img


SLIDE_FUNCS = [slide_10, slide_11, slide_12, slide_13, slide_14, slide_15, slide_16]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT_DIR / "raw_backgrounds"
    raw_dir.mkdir(exist_ok=True)

    final_paths = []
    for idx, (bg, func) in enumerate(zip(BG_PATHS, SLIDE_FUNCS), 10):
        raw_copy = raw_dir / f"slide_{idx:02d}_background.png"
        shutil.copy2(bg, raw_copy)
        img = crop_16x9(Image.open(bg))
        img = func(img)
        out = OUT_DIR / f"slide_{idx:02d}.png"
        img.convert("RGB").save(out, quality=96)
        final_paths.append(out)

    thumb_w, thumb_h = 480, 270
    sheet = Image.new("RGB", (thumb_w * 4, thumb_h * 2), "white")
    for idx, path in enumerate(final_paths):
        im = Image.open(path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(im, ((idx % 4) * thumb_w, (idx // 4) * thumb_h))
    sheet.save(OUT_DIR / "contact_sheet_10_16.jpg", quality=92)
    print("\n".join(str(p) for p in final_paths))
    print(OUT_DIR / "contact_sheet_10_16.jpg")


if __name__ == "__main__":
    main()
