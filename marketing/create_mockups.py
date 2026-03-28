"""
SelfCore Marketing Mockup Generator
Creates 5 polished marketing images using pure Pillow.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
W, H = 1270, 760

# ─── Colors ──────────────────────────────────
BG = "#0F172A"
CARD = "#1E293B"
CARD2 = "#162032"
CYAN = "#58E6FF"
WHITE = "#FFFFFF"
GRAY = "#94A3B8"
DARK_GRAY = "#475569"
GREEN = "#4ADE80"
RED = "#F87171"
BLUE = "#4285F4"
ORANGE = "#FB923C"
PURPLE = "#A78BFA"
ACCENT2 = "#38BDF8"

# ─── Font helper ─────────────────────────────
def get_font(size):
    """Try system fonts, fall back to default."""
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]
    for f in candidates:
        if os.path.isfile(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_bold_font(size):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]
    for f in candidates:
        if os.path.isfile(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return get_font(size)

def get_korean_font(size):
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "C:/Windows/Fonts/batang.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for f in candidates:
        if os.path.isfile(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return get_font(size)


def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    r = radius
    # Fill
    if fill:
        draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
        draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
        draw.pieslice([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill)
        draw.pieslice([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill)
        draw.pieslice([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill)
        draw.pieslice([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill)
    if outline:
        draw.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=outline, width=width)
        draw.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=outline, width=width)
        draw.line([x0+r, y0, x1-r, y0], fill=outline, width=width)
        draw.line([x0+r, y1, x1-r, y1], fill=outline, width=width)
        draw.line([x0, y0+r, x0, y1-r], fill=outline, width=width)
        draw.line([x1, y0+r, x1, y1-r], fill=outline, width=width)


def dim_color(hex_color, factor=0.25):
    """Create a darkened version of a color for chip backgrounds."""
    hex_color = hex_color.lstrip("#")[:6]
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    # Blend toward BG color (#0F172A)
    bg_r, bg_g, bg_b = 15, 23, 42
    nr = int(bg_r + (r - bg_r) * factor)
    ng = int(bg_g + (g - bg_g) * factor)
    nb = int(bg_b + (b - bg_b) * factor)
    return f"#{nr:02x}{ng:02x}{nb:02x}"

def draw_chip(draw, x, y, text, bg_color, text_color=WHITE, font=None):
    """Draw a pill-shaped chip/tag."""
    if font is None:
        font = get_font(16)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 14, 6
    chip_w = tw + pad_x * 2
    chip_h = th + pad_y * 2
    # Fix: use proper dimmed color instead of hex+alpha
    safe_bg = bg_color if len(bg_color) <= 7 else dim_color(bg_color[:7])
    rounded_rect(draw, [x, y, x + chip_w, y + chip_h], radius=chip_h // 2, fill=safe_bg)
    draw.text((x + pad_x, y + pad_y - 2), text, fill=text_color, font=font)
    return chip_w


def draw_platform_circle(draw, cx, cy, r, letter, color, font=None):
    """Draw a colored circle with a letter."""
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=color)
    if font is None:
        font = get_bold_font(int(r * 1.1))
    bbox = font.getbbox(letter)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw//2, cy - th//2 - 2), letter, fill=BG if color != WHITE else "#000000", font=font)


# ═══════════════════════════════════════════════════════════════
# IMAGE 1: Hero
# ═══════════════════════════════════════════════════════════════
def create_hero():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = get_bold_font(64)
    subtitle_font = get_font(24)
    label_font = get_font(18)
    value_font = get_bold_font(18)
    small_font = get_font(16)
    kr_font = get_korean_font(18)

    # Title
    draw.text((W//2, 60), "SelfCore", fill=WHITE, font=title_font, anchor="mt")
    draw.text((W//2, 135), "Own your AI identity. One file. Every AI.", fill=GRAY, font=subtitle_font, anchor="mt")

    # Profile card mockup
    card_x, card_y = 235, 200
    card_w, card_h = 800, 340
    rounded_rect(draw, [card_x, card_y, card_x+card_w, card_y+card_h], radius=16, fill=CARD, outline="#334155", width=1)

    # Card title bar
    draw.ellipse([card_x+16, card_y+16, card_x+28, card_y+28], fill="#EF4444")
    draw.ellipse([card_x+36, card_y+16, card_x+48, card_y+28], fill="#EAB308")
    draw.ellipse([card_x+56, card_y+16, card_x+68, card_y+28], fill="#22C55E")
    draw.text((card_x + 90, card_y + 14), "SelfCore - Profile Editor", fill=DARK_GRAY, font=small_font)

    # Divider
    draw.line([card_x+16, card_y+44, card_x+card_w-16, card_y+44], fill="#334155", width=1)

    # Profile fields
    fields = [
        ("Name", "Jeong Min"),
        ("Role", "Full-stack Developer"),
        ("Project", "SelfCore (Electron + Python + React)"),
        ("Tech Stack", "Python, TypeScript, React, spaCy, Electron"),
        ("Language", "Korean / English"),
    ]
    y = card_y + 60
    for label, value in fields:
        draw.text((card_x + 40, y), label, fill=CYAN, font=label_font)
        draw.text((card_x + 200, y), value, fill=WHITE, font=value_font)
        y += 42

    # Preferences section
    y += 10
    draw.text((card_x + 40, y), "Preferences", fill=CYAN, font=label_font)
    chip_x = card_x + 200
    for tag, color in [("Python", GREEN), ("React", BLUE), ("Privacy", PURPLE), ("Local-first", ORANGE)]:
        cw = draw_chip(draw, chip_x, y - 2, tag, color + "33", color, small_font)
        chip_x += cw + 8

    # Platform circles at bottom
    platforms = [
        ("C", CYAN, "Claude"),
        ("G", GREEN, "ChatGPT"),
        ("Ge", BLUE, "Gemini"),
        ("X", WHITE, "Grok"),
        ("M", ORANGE, "Mistral"),
    ]
    circle_y = 610
    start_x = W // 2 - (len(platforms) - 1) * 90 // 2
    platform_font = get_bold_font(16)
    name_font = get_font(13)
    for i, (letter, color, name) in enumerate(platforms):
        cx = start_x + i * 90
        draw_platform_circle(draw, cx, circle_y, 24, letter, color, platform_font)
        draw.text((cx, circle_y + 34), name, fill=GRAY, font=name_font, anchor="mt")

    # Bottom text
    draw.text((W//2, H - 40), "100% Local  \u2022  Zero Cloud  \u2022  Your Data", fill=DARK_GRAY, font=subtitle_font, anchor="mm")

    img.save(os.path.join(OUTPUT_DIR, "hero.png"), "PNG")
    print(f"[1/5] hero.png created ({W}x{H})")


# ═══════════════════════════════════════════════════════════════
# IMAGE 2: Injection Demo
# ═══════════════════════════════════════════════════════════════
def create_injection():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = get_bold_font(36)
    body_font = get_font(16)
    bold_font = get_bold_font(16)
    small_font = get_font(14)
    kr_font = get_korean_font(16)
    arrow_font = get_bold_font(48)

    # Title
    draw.text((W//2, 35), "Context Injection", fill=WHITE, font=title_font, anchor="mt")
    draw.text((W//2, 80), "Press Ctrl+Shift+Space. Every AI knows you instantly.", fill=GRAY, font=body_font, anchor="mt")

    # Left: SelfCore mini window
    lx, ly = 60, 130
    lw, lh = 380, 480
    rounded_rect(draw, [lx, ly, lx+lw, ly+lh], radius=12, fill=CARD, outline="#334155", width=1)
    # Title bar
    draw.ellipse([lx+12, ly+12, lx+22, ly+22], fill="#EF4444")
    draw.ellipse([lx+28, ly+12, lx+38, ly+22], fill="#EAB308")
    draw.ellipse([lx+44, ly+12, lx+54, ly+22], fill="#22C55E")
    draw.text((lx + 66, ly + 10), "SelfCore Profile", fill=DARK_GRAY, font=small_font)
    draw.line([lx+12, ly+36, lx+lw-12, ly+36], fill="#334155", width=1)

    profile_lines = [
        ("Name:", "Jeong Min"),
        ("Role:", "Developer"),
        ("Stack:", "Python, React, Electron"),
        ("Prefs:", "Privacy-first, Korean"),
        ("Project:", "SelfCore v1.0"),
    ]
    py = ly + 50
    for label, val in profile_lines:
        draw.text((lx + 24, py), label, fill=CYAN, font=bold_font)
        draw.text((lx + 110, py), val, fill=WHITE, font=body_font)
        py += 32

    # .self file icon
    py += 20
    rounded_rect(draw, [lx+24, py, lx+lw-24, py+50], radius=8, fill="#0F172A", outline=CYAN, width=1)
    draw.text((lx + lw//2, py + 25), "profile.self  (AES-256 encrypted)", fill=CYAN, font=small_font, anchor="mm")

    # Status
    py += 70
    draw.ellipse([lx+24, py+2, lx+36, py+14], fill=GREEN)
    draw.text((lx + 44, py), "Ready  \u2014  Context generated (183 tokens)", fill=GREEN, font=small_font)

    # Center: Arrow
    ax = W // 2
    ay = H // 2 - 20
    draw.text((ax, ay - 20), "Ctrl+Shift+Space", fill=CYAN, font=bold_font, anchor="mm")
    # Draw arrow
    draw.line([ax-30, ay+20, ax+30, ay+20], fill=CYAN, width=3)
    draw.polygon([(ax+30, ay+10), (ax+50, ay+20), (ax+30, ay+30)], fill=CYAN)

    # Right: Chat interface mockup
    rx, ry = 530, 130
    rw, rh = 680, 480
    rounded_rect(draw, [rx, ry, rx+rw, ry+rh], radius=12, fill=CARD, outline="#334155", width=1)
    # Title bar
    draw.ellipse([rx+12, ry+12, rx+22, ry+22], fill="#EF4444")
    draw.ellipse([rx+28, ry+12, rx+38, ry+22], fill="#EAB308")
    draw.ellipse([rx+44, ry+12, rx+54, ry+22], fill="#22C55E")
    draw.text((rx + 66, ry + 10), "Claude.ai", fill=DARK_GRAY, font=small_font)
    draw.line([rx+12, ry+36, rx+rw-12, ry+36], fill="#334155", width=1)

    # Injected context (highlighted)
    ctx_y = ry + 50
    rounded_rect(draw, [rx+16, ctx_y, rx+rw-16, ctx_y+120], radius=8, fill="#0C2D48", outline="#3A8A99", width=1)
    draw.text((rx+28, ctx_y+8), "[SelfCore Context]", fill=CYAN, font=bold_font)
    ctx_lines = [
        "The user is Jeong Min, a full-stack developer.",
        "Tech: Python, TypeScript, React, Electron.",
        "Preferences: Korean language, privacy-first.",
        "Current project: SelfCore (AI identity engine).",
    ]
    for i, line in enumerate(ctx_lines):
        draw.text((rx+28, ctx_y + 30 + i*20), line, fill=ACCENT2, font=small_font)

    # User message
    msg_y = ctx_y + 140
    rounded_rect(draw, [rx+rw-320, msg_y, rx+rw-16, msg_y+36], radius=18, fill="#2563EB")
    draw.text((rx+rw-168, msg_y+18), "Help me fix the Electron bug", fill=WHITE, font=small_font, anchor="mm")

    # AI response
    ai_y = msg_y + 52
    rounded_rect(draw, [rx+16, ai_y, rx+500, ai_y+100], radius=12, fill="#162032")
    kr_resp_font = get_korean_font(15)
    resp_lines = [
        "Sure, Jeong Min! Since you're working on",
        "SelfCore with Electron + Python, I can see",
        "the main.js crash issue. Here's the fix for",
        "the single-instance lock problem...",
    ]
    for i, line in enumerate(resp_lines):
        draw.text((rx+30, ai_y+12 + i*22), line, fill=WHITE, font=small_font)

    # Caption
    draw.text((W//2, H - 35), "Your AI identity follows you across every platform.", fill=DARK_GRAY, font=body_font, anchor="mm")

    img.save(os.path.join(OUTPUT_DIR, "injection.png"), "PNG")
    print(f"[2/5] injection.png created ({W}x{H})")


# ═══════════════════════════════════════════════════════════════
# IMAGE 3: Analysis Engine
# ═══════════════════════════════════════════════════════════════
def create_analysis():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = get_bold_font(36)
    body_font = get_font(16)
    bold_font = get_bold_font(16)
    small_font = get_font(14)
    label_font = get_bold_font(14)
    chip_font = get_font(15)

    # Title
    draw.text((W//2, 35), "Smart Analysis Engine", fill=WHITE, font=title_font, anchor="mt")
    draw.text((W//2, 80), "Import your AI history. SelfCore understands you in 15 seconds.", fill=GRAY, font=body_font, anchor="mt")

    # Left: Upload area
    lx, ly = 40, 130
    lw, lh = 300, 430
    rounded_rect(draw, [lx, ly, lx+lw, ly+lh], radius=12, fill=CARD, outline="#334155", width=1)
    draw.text((lx + lw//2, ly + 20), "Import Data", fill=WHITE, font=bold_font, anchor="mt")
    draw.line([lx+16, ly+48, lx+lw-16, ly+48], fill="#334155", width=1)

    files = [
        ("ChatGPT Export.zip", GREEN, "1.2 MB"),
        ("Claude Conversations.json", PURPLE, "840 KB"),
        ("Gemini Takeout.zip", BLUE, "2.1 MB"),
        ("Grok Archive.zip", WHITE, "560 KB"),
    ]
    fy = ly + 65
    for fname, color, size in files:
        rounded_rect(draw, [lx+16, fy, lx+lw-16, fy+52], radius=8, fill="#0F172A")
        # File icon
        draw.rectangle([lx+28, fy+12, lx+44, fy+40], fill=dim_color(color, 0.3), outline=color, width=1)
        draw.text((lx + 56, fy + 10), fname, fill=WHITE, font=small_font)
        draw.text((lx + 56, fy + 30), size, fill=DARK_GRAY, font=small_font)
        # Check mark
        draw.text((lx+lw-36, fy+18), "\u2713", fill=GREEN, font=bold_font)
        fy += 62

    # Processing status
    fy += 16
    draw.text((lx + lw//2, fy), "4 sources merged", fill=GREEN, font=bold_font, anchor="mt")
    draw.text((lx + lw//2, fy + 24), "2,847 messages analyzed", fill=GRAY, font=small_font, anchor="mt")

    # Center: Pipeline
    px = 370
    py = 300
    # Arrow line
    draw.line([px, py+20, px+140, py+20], fill=CYAN, width=2)
    draw.polygon([(px+140, py+10), (px+160, py+20), (px+140, py+30)], fill=CYAN)

    pipeline_steps = ["spaCy NLP", "TF-IDF", "Ollama AI"]
    for i, step in enumerate(pipeline_steps):
        sx = px + 10
        sy = py + 50 + i * 40
        rounded_rect(draw, [sx, sy, sx+130, sy+30], radius=15, fill=dim_color(CYAN, 0.2), outline=CYAN, width=1)
        draw.text((sx+65, sy+15), step, fill=CYAN, font=small_font, anchor="mm")

    # Right: Results
    rx, ry = 560, 130
    rw, rh = 670, 430
    rounded_rect(draw, [rx, ry, rx+rw, ry+rh], radius=12, fill=CARD, outline="#334155", width=1)
    draw.text((rx + rw//2, ry + 20), "Extracted Profile", fill=WHITE, font=bold_font, anchor="mt")
    draw.line([rx+16, ry+48, rx+rw-16, ry+48], fill="#334155", width=1)

    # Tech Tags
    draw.text((rx+24, ry+62), "Tech Stack", fill=CYAN, font=label_font)
    tag_x = rx + 24
    tag_y = ry + 84
    for tag in ["Python", "TypeScript", "React", "Electron", "spaCy", "Next.js", "PostgreSQL"]:
        cw = draw_chip(draw, tag_x, tag_y, tag, CYAN+"22", CYAN, chip_font)
        tag_x += cw + 6
        if tag_x > rx + rw - 80:
            tag_x = rx + 24
            tag_y += 32

    # Preferences
    pref_y = tag_y + 50
    draw.text((rx+24, pref_y), "Preferences", fill=CYAN, font=label_font)
    prefs = [
        ("Python", GREEN, "+"), ("Privacy", GREEN, "+"), ("Local-first", GREEN, "+"),
        ("Cloud storage", RED, "-"), ("Java", RED, "-"),
    ]
    px2 = rx + 24
    for pname, color, sign in prefs:
        label = f"{sign} {pname}"
        cw = draw_chip(draw, px2, pref_y + 24, label, color+"22", color, chip_font)
        px2 += cw + 6

    # Topics
    topic_y = pref_y + 75
    draw.text((rx+24, topic_y), "Topics (TF-IDF)", fill=CYAN, font=label_font)
    kr_font = get_korean_font(14)
    topics = [
        ("Frontend Development", 0.92),
        ("AI/ML Engineering", 0.87),
        ("Privacy & Security", 0.74),
        ("Open Source", 0.68),
    ]
    for i, (topic, score) in enumerate(topics):
        ty = topic_y + 26 + i * 32
        # Bar background
        bar_w = int(280 * score)
        rounded_rect(draw, [rx+24, ty, rx+24+280, ty+22], radius=11, fill="#0F172A")
        rounded_rect(draw, [rx+24, ty, rx+24+bar_w, ty+22], radius=11, fill=dim_color(CYAN, 0.35))
        draw.text((rx+32, ty+3), topic, fill=WHITE, font=small_font)
        draw.text((rx+314, ty+3), f"{score:.0%}", fill=CYAN, font=small_font)

    # Communication style
    style_y = topic_y + 160
    draw.text((rx+24, style_y), "Communication Style", fill=CYAN, font=label_font)
    styles = [("Directness: 82%", "Technical depth: 91%"), ("Formality: 45%", "Avg length: 67 words")]
    sy2 = style_y + 24
    for left, right in styles:
        draw.text((rx+24, sy2), left, fill=WHITE, font=small_font)
        draw.text((rx+240, sy2), right, fill=WHITE, font=small_font)
        sy2 += 24

    # Caption
    draw.text((W//2, H - 35), "Automatic profile generation from your existing AI conversations.", fill=DARK_GRAY, font=body_font, anchor="mm")

    img.save(os.path.join(OUTPUT_DIR, "analysis.png"), "PNG")
    print(f"[3/5] analysis.png created ({W}x{H})")


# ═══════════════════════════════════════════════════════════════
# IMAGE 4: Privacy
# ═══════════════════════════════════════════════════════════════
def create_privacy():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = get_bold_font(36)
    body_font = get_font(16)
    bold_font = get_bold_font(18)
    small_font = get_font(15)
    big_font = get_bold_font(24)

    # Title
    draw.text((W//2, 35), "Your AI Identity Belongs to You", fill=WHITE, font=title_font, anchor="mt")
    draw.text((W//2, 80), "Not Big Tech.", fill=GRAY, font=body_font, anchor="mt")

    # Center lock icon (drawn with shapes)
    cx, cy = W//2, 280
    # Lock body
    rounded_rect(draw, [cx-60, cy, cx+60, cy+80], radius=10, fill=CYAN)
    # Lock shackle (arc)
    draw.arc([cx-35, cy-50, cx+35, cy+10], 180, 360, fill=CYAN, width=8)
    # Keyhole
    draw.ellipse([cx-10, cy+25, cx+10, cy+45], fill=BG)
    draw.rectangle([cx-5, cy+40, cx+5, cy+60], fill=BG)

    # Feature labels around lock
    features = [
        (cx - 340, cy - 20, "100% Local Processing"),
        (cx + 180, cy - 20, "Zero Server Communication"),
        (cx - 340, cy + 50, "AES-256 Encrypted"),
        (cx + 180, cy + 50, "You Own Your Data"),
    ]
    for fx, fy, text in features:
        rounded_rect(draw, [fx, fy, fx+280, fy+44], radius=22, fill=CARD, outline="#334155", width=1)
        # Dot
        draw.ellipse([fx+14, fy+16, fx+26, fy+28], fill=CYAN)
        draw.text((fx + 36, fy + 12), text, fill=WHITE, font=small_font)

    # Comparison table
    ty = 420
    table_x = 185
    table_w = 900
    rounded_rect(draw, [table_x, ty, table_x+table_w, ty+240], radius=12, fill=CARD, outline="#334155", width=1)

    # Header
    draw.text((table_x + table_w//4, ty + 18), "Platform Memory", fill=GRAY, font=bold_font, anchor="mt")
    draw.text((table_x + 3*table_w//4, ty + 18), "SelfCore", fill=CYAN, font=bold_font, anchor="mt")
    draw.line([table_x+16, ty+48, table_x+table_w-16, ty+48], fill="#334155", width=1)
    draw.line([table_x+table_w//2, ty+48, table_x+table_w//2, ty+230], fill="#334155", width=1)

    rows = [
        ("ChatGPT Memory", "Cloud servers", "Your PC only"),
        ("Claude Memory", "Cloud servers", "Your PC only"),
        ("Data Ownership", "Platform owns it", "You own it"),
        ("Portability", "Locked in", "Works everywhere"),
        ("Encryption", "Their keys", "Your keys (AES-256)"),
    ]
    ry = ty + 58
    for label, cloud, local in rows:
        mid = table_x + table_w // 2
        draw.text((table_x + 24, ry + 4), label, fill=WHITE, font=small_font)
        draw.text((mid - 20, ry + 4), cloud, fill=RED, font=small_font, anchor="rt")
        draw.ellipse([mid - 14, ry + 7, mid - 4, ry + 17], fill=RED)
        draw.text((mid + 24, ry + 4), local, fill=GREEN, font=small_font)
        draw.ellipse([mid + 10, ry + 7, mid + 20, ry + 17], fill=GREEN)
        ry += 36

    # Caption
    draw.text((W//2, H - 35), "Privacy by design. No telemetry. No analytics. No compromise.", fill=DARK_GRAY, font=body_font, anchor="mm")

    img.save(os.path.join(OUTPUT_DIR, "privacy.png"), "PNG")
    print(f"[4/5] privacy.png created ({W}x{H})")


# ═══════════════════════════════════════════════════════════════
# IMAGE 5: Platform Support
# ═══════════════════════════════════════════════════════════════
def create_platforms():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    title_font = get_bold_font(36)
    body_font = get_font(16)
    bold_font = get_bold_font(16)
    small_font = get_font(14)
    name_font = get_bold_font(20)
    check_font = get_font(13)

    # Title
    draw.text((W//2, 35), "One Profile. Five Platforms. Zero Lock-in.", fill=WHITE, font=title_font, anchor="mt")

    # Center: SelfCore hub
    cx, cy = W//2, 340
    # Glow effect
    for i in range(5, 0, -1):
        alpha = 20 + i * 5
        draw.ellipse([cx-55-i*4, cy-55-i*4, cx+55+i*4, cy+55+i*4], fill=f"#0C2D48")
    draw.ellipse([cx-55, cy-55, cx+55, cy+55], fill=CARD, outline=CYAN, width=2)
    sc_font = get_bold_font(22)
    draw.text((cx, cy - 8), "Self", fill=WHITE, font=sc_font, anchor="mm")
    draw.text((cx, cy + 14), "Core", fill=CYAN, font=sc_font, anchor="mm")

    # Platforms around the center
    platforms = [
        ("Claude", CYAN, "C", -200, -180),
        ("ChatGPT", GREEN, "G", 200, -180),
        ("Gemini", BLUE, "Ge", -320, 60),
        ("Grok", "#E7E9EA", "X", 320, 60),
        ("Mistral", ORANGE, "M", 0, 220),
    ]

    for pname, color, letter, ox, oy in platforms:
        px, py = cx + ox, cy + oy
        # Connection line
        draw.line([cx, cy, px, py], fill="#334155", width=1)
        # Dotted effect
        dx = px - cx
        dy = py - cy
        for t in [0.3, 0.5, 0.7]:
            dot_x = cx + dx * t
            dot_y = cy + dy * t
            draw.ellipse([dot_x-2, dot_y-2, dot_x+2, dot_y+2], fill=dim_color(CYAN, 0.5))

        # Platform circle
        draw_platform_circle(draw, px, py, 32, letter, color, get_bold_font(20))
        # Name
        draw.text((px, py + 44), pname, fill=WHITE, font=name_font, anchor="mt")

        # Import + Inject badges
        features_text = "Import \u2713  Inject \u2713"
        if pname == "Mistral":
            features_text = "Inject \u2713"
        draw.text((px, py + 70), features_text, fill=GREEN, font=check_font, anchor="mt")

    # Bottom features
    features = [
        "Chrome Extension Auto-Inject",
        "Ctrl+Shift+Space Shortcut",
        "Drag & Drop Import",
        "Korean + English",
    ]
    fy = H - 100
    fx_start = W // 2 - (len(features) * 150) // 2
    for i, feat in enumerate(features):
        fx = fx_start + i * 170 + 85
        rounded_rect(draw, [fx-75, fy, fx+75, fy+30], radius=15, fill=CARD, outline="#334155", width=1)
        draw.text((fx, fy+15), feat, fill=GRAY, font=check_font, anchor="mm")

    # Caption
    draw.text((W//2, H - 30), "Your identity follows you. No platform lock-in.", fill=DARK_GRAY, font=body_font, anchor="mm")

    img.save(os.path.join(OUTPUT_DIR, "platforms.png"), "PNG")
    print(f"[5/5] platforms.png created ({W}x{H})")


# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Creating SelfCore marketing mockups...")
    create_hero()
    create_injection()
    create_analysis()
    create_privacy()
    create_platforms()
    print(f"\nAll 5 images saved to: {OUTPUT_DIR}")
