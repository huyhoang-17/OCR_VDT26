---
name: viettel-pptx
description: >
  Create or edit PowerPoint presentations (.pptx) that strictly follow the Viettel Software
  corporate brand design system. Use this skill whenever the user asks to create slides,
  a deck, a presentation, or modify .pptx files AND the context is Viettel Software —
  including internal training decks, project presentations, proposal slides, or any deck
  that should carry the Viettel Software visual identity (red #EE1A2E, gray palette,
  PF BeauSans Pro for headings + Sarabun for body, footer bar). Also trigger when user says "làm slide", "tạo deck",
  "thiết kế presentation", "slide Viettel", or uploads a Viettel-branded .pptx.
  Always use this skill over the generic pptx skill when Viettel brand context is present.
---

# Viettel Software PPTX Skill

This skill extends the base `pptx` skill with Viettel Software brand enforcement.
**Always read `/mnt/skills/public/pptx/SKILL.md` first** for tooling setup, then apply
the brand rules in this file on top.

> ⚠️ All values below are **extracted directly from BM04 template** — verified pixel-level.
> Do not substitute old/assumed values.

---

## Brand Quick Reference

| Token | Value | Source |
|---|---|---|
| Primary Red | `#EE1A2E` | Most-used red (19× across content slides) |
| Accent Red | `#EE0033` | Cover subtitle label, closing title |
| Footer Red (right panel) | `#ED1B2F` | Sampled directly from `footer_bar.png` |
| Footer BG (left panel) | `#F3F3F4` | Sampled directly from `footer_bar.png` |
| Primary Text | `#000000` | Theme dk1 |
| Gray Dark | `#5A5A5A` | Content shape fills (secondary) |
| Gray Mid | `#808080` | Content shape fills — most-used gray (20×) |
| Gray Light | `#B4B4B4` | Footer URL text, light accents |
| Gray Pale | `#E6E6E6` | Lightest fills, decorative circles |
| Background | `#FFFFFF` | All content slides |
| Theme dk2 | `#42494D` | Only in theme XML — not used as direct fill |
| Heading Font | **PF BeauSans Pro** — for all titles, section dividers, shape labels |
| Body Font | **Sarabun** — for body text, subtitles, descriptions, footer URL |
| Title Font | PF BeauSans Pro **Bold**, 45pt, ALL CAPS, `#EE1A2E`, centered |
| Subtitle Font | Sarabun Regular, 18pt, letter-spaced, dark, centered |
| Body Font | Sarabun Regular, 18pt, Sentence case |
| Shape Label | PF BeauSans Pro Bold, 17–18pt, white |
| Cover Main Title | PF BeauSans Pro Regular, 44pt, `#FFFFFF` |
| Section Divider Title | PF BeauSans Pro Bold, 48pt, `#FFFFFF` |
| Closing Title | PF BeauSans Pro Regular, 51pt, `#EE0033` |
| Footer URL | Sarabun Regular, 21pt, `#B4B4B4` |
| Slide Size | 1440 × 810 pt (20" × 11.25", 16:9) |
| Safe Margins | 36pt (0.5") all sides |
| Footer Y | **10.259"** (738.7pt from top) |
| Footer H | **0.991"** (71.3pt) |

---

## Asset Files (Bundled — always use, never re-draw as shapes)

Path prefix: `/mnt/skills/user/viettel-pptx/assets/`

| File | Dimensions | Description | Used on |
|---|---|---|---|
| `logo.png` | 2000×683 | Full-color Viettel Software logo (dark text + red) | General use |
| `logo_white.png` | 253×102 | White Viettel Software logo, transparent bg | Footer right (on red) |
| `footer_bar.png` | 1613×95 | Complete footer strip: left `#F3F3F4`, right `#ED1B2F` | **Every slide** |
| `cover_title_pill.png` | 810×188 | Red rounded rectangle pill for cover main title bg | Cover slide |
| `cover_subtitle_pill.png` | 683×113 | Light gray pill for cover category/subtitle label | Cover slide |
| `section_blob.png` | 973×624 | Red organic blob for section divider text background | Section divider |

### Bundled Fonts

Path prefix: `/mnt/skills/user/viettel-pptx/assets/fonts/`

| Folder | Family | Weights available | Used for |
|---|---|---|---|
| `beausanspro/` | **PF BeauSans Pro** | XThin, Thin, Light, Regular, Bbook, SemiBold, Bold, Black (+ italics) | All headings & titles |
| `sarabun/` | **Sarabun** | Thin, ExtraLight, Light, Regular, Medium, SemiBold, Bold, ExtraBold (+ italics) | Body text, subtitles, footer URL, descriptions |

> ⚠️ Fonts must be **installed on the rendering machine** for PowerPoint to display them correctly.
> The .ttf files are bundled here so they can be installed once (`fc-cache -f` on Linux, drag to Font Book on macOS, or right-click → Install on Windows).
> If a font is missing on the user's system, PowerPoint will fall back to a default font and the deck will not match the brand.

---

## Slide Anatomy

### Footer Bar (REQUIRED on EVERY slide — render last)

The footer is built from **layered images**, not drawn shapes:

```
1. footer_bar.png  x=0       y=10.259"  w=20"     h=0.991"
   → full-width strip: left ~80% #F3F3F4, right ~20% #ED1B2F
2. logo_white.png  x=17.22"  y=10.435"  w=1.847"  h=0.745"
   → white logo sitting on the red zone
3. Text "www.viettel.com.vn"
   x=0.549"  y=10.477"  w=8.681"  h=0.454"
   21pt Sarabun Regular, color #B4B4B4, align left
```

**Never remove, resize, or cover. Never re-create as shapes.**

### Content Safe Area
All content must stay within **y < 10.0"** (720pt) to avoid overlapping the footer.

---

## Decorative Background Shapes (Optional)

Để slide trắng không bị đơn điệu, có thể thêm **shape trang trí mờ ở góc/cạnh** trước khi vẽ nội dung. Background này **hoàn toàn tùy chọn** — slide không có cũng vẫn hợp brand. Khi dùng phải tuân thủ nguyên tắc:

**Quy tắc bắt buộc:**

1. **Z-order**: gọi `addBackground(slide, variant)` **ngay sau khi tạo slide**, trước mọi nội dung khác. Footer vẫn được gọi cuối cùng và đè lên background.
2. **Vùng cấm**: không có shape trang trí nào được nằm trong vùng nội dung trung tâm (`x: 2"–18", y: 1.5"–9.5"`). Chỉ được phép ở góc và cạnh.
3. **Opacity**: tất cả shape decorative phải có `transparency: 85` trở lên (PptxGenJS dùng `transparency` 0–100, trong đó 100 = trong suốt hoàn toàn). Hoặc dùng trực tiếp màu pale như `#E6E6E6` ở 100% opacity.
4. **Không text/icon overlap**: nếu shape đè lên text hoặc icon, **bỏ shape đó** — text quan trọng hơn trang trí.
5. **Bỏ trên cover & section divider**: cover và section divider đã có hình ảnh full-bleed → **không** thêm background trang trí. Chỉ dùng cho content slide.
6. **Tối đa 2 shape mỗi slide**: nhẹ nhàng, không gây phân tâm.

**Bảng màu được phép (chỉ những giá trị này, không tự ý chế biến):**

| Token | Hex | Khi nào dùng |
|---|---|---|
| Gray Pale | `#E6E6E6` | Mặc định — an toàn nhất, dùng được mọi slide |
| Gray Light | `#B4B4B4` | Chỉ khi shape rất nhỏ (<1.5") và cần đậm hơn pale |
| Red Watermark | `#EE1A2E` @ `transparency: 92` | Slide nội dung quan trọng, slide mở đầu chương, slide closing-style |
| Red Accent | `#EE0033` @ `transparency: 92` | Hiếm — chỉ cho slide highlight đặc biệt |

**6 Background Variants:**

| Variant | Mô tả | Phù hợp slide |
|---|---|---|
| `'none'` | Không background, trắng trơn | Diagram dense, Venn, chevron flow |
| `'corner-tr'` | 1 hình tròn pale lớn ở góc trên phải | Content slide thông thường, intro |
| `'corner-bl'` | 1 hình tròn pale lớn ở góc dưới trái | Content slide có heading mạnh ở trên |
| `'dual-corners'` | 2 hình tròn pale ở góc đối nhau (TR + BL) | Slide ít text, cần "đỡ" 2 góc |
| `'side-arc-left'` | Arc/quarter circle pale ở cạnh trái | Slide có list dọc bên trái |
| `'red-watermark'` | Hình tròn red mờ rất lớn ở góc, tạo accent | Slide mở chương, slide thông điệp |

---

## Slide Type Templates

### Cover Slide
```
[Photo full-bleed: x=0, y=0, w=20", h=11.25"]
  ↓
[cover_subtitle_pill.png: x=0, y=4.306", w=6.216", h=1.024"]
[Category text: x=0.2", y=4.518", w=6.0", h=0.64" | 20pt, #EE0033, left]
  ↓
[cover_title_pill.png: x=1.209", y=5.625", w=7.361", h=1.706"]
[Title text: x=1.621", y=6.007", w=6.536", h=0.841" | 44pt, white, center]
  ↓
[addFooter()]
```

### Section Divider
```
[Photo left panel: x=0, y=0, w=9.194", h=10.072"]   ← ~46% width
[section_blob.png: x=7.446", y=2.601", w=7.575", h=4.858"]  ← overlaps photo edge
[Section title: x=8.861", y=3.452", w=4.661", h=3.063" | 48pt, white, center, bold]
[addFooter()]
```

### Content / Diagram Slide
```
[addBackground(slide, 'corner-tr')]   ← OPTIONAL, call first; use 'none' for dense diagrams
[Title: centered, y=0.502", 45pt PF BeauSans Pro Bold, #EE1A2E, ALL CAPS]
[Subtitle: centered, y=1.292", 18pt Sarabun Regular]
[Content area: y from ~2.0" to ~9.8" — shapes, diagrams, icons]
  Shape fills:
    Primary   → #EE1A2E (red), white text
    Secondary → #5A5A5A (dark gray), white text
    Tertiary  → #808080 (mid gray), white text
    Light     → #E6E6E6 (pale), dark text
[addFooter()]
```

### Process / Steps Slide
```
3 rows stacked vertically (~2" apart each):
  [Circle ~1.2" dia] [Rounded-rect title ~4" wide] [Rounded-rect body ~7" wide]
  Row 1: #EE1A2E circle | #EE1A2E title rect | #EE1A2E body rect (lighter: add alpha)
  Row 2: #808080 circle | #808080 title rect | #808080 body rect
  Row 3: #5A5A5A circle | #5A5A5A title rect | #5A5A5A body rect
  Step number in circle: 36–48pt Bold white
```

### Chevron / Flow Slide
```
4 chevron/arrow shapes left→right, each with icon + bold white title:
  Arrow 1 (emphasized): #EE1A2E
  Arrow 2: #5A5A5A
  Arrow 3: #808080
  Arrow 4: #B4B4B4
Description text block below each arrow
```

### Venn Diagram Slide
```
3 overlapping circles:
  Left:         #EE1A2E, "1" white bold
  Top-right:    #5A5A5A, "2" white bold
  Bottom-center:#808080, "3" white bold
Label + description outside each circle
```

### Closing Slide
```
[Large decorative circle left: ~6" dia, #E6E6E6 fill]
["XIN TRÂN TRỌNG\nCẢM ƠN" on left: 51pt PF BeauSans Pro, #EE0033, x≈0.4", y≈4.3"]
[3 dots decoration: gray / red / dark — below title text]
[Concentric rings + circular photo: right side, x≈9", w≈8"]
[addFooter() — note: footer bg is gray here, no extra overlay needed]
```

---

## PptxGenJS Brand Constants

```javascript
const fs   = require('fs');
const path = require('path');

// ── LOAD ASSETS ────────────────────────────────────────────────────────────
const ASSETS = '/mnt/skills/user/viettel-pptx/assets/';
const loadB64 = (name) => fs.readFileSync(path.join(ASSETS, name)).toString('base64');

const FOOTER_BAR_B64    = loadB64('footer_bar.png');
const LOGO_WHITE_B64    = loadB64('logo_white.png');
const COVER_PILL_B64    = loadB64('cover_title_pill.png');
const COVER_SUB_B64     = loadB64('cover_subtitle_pill.png');
const SECTION_BLOB_B64  = loadB64('section_blob.png');

// ── BRAND COLORS ──────────────────────────────────────────────────────────
const BRAND = {
  red:       'EE1A2E',  // primary — titles, primary shapes
  redAccent: 'EE0033',  // cover label, closing title
  gray1:     '5A5A5A',  // dark gray fills
  gray2:     '808080',  // mid gray fills (most used)
  gray3:     'B4B4B4',  // footer URL, light accents
  gray4:     'E6E6E6',  // palest fills, decorative
  white:     'FFFFFF',
  black:     '000000',
};

// ── FONTS ──────────────────────────────────────────────────────────────────
// Headings/titles → 'PF BeauSans Pro'  | Body/labels → 'Sarabun'
// The exact font names below must match the font family name as installed on
// the system (case-sensitive). PowerPoint will fall back to a default if missing.
const FONT_HEAD = 'PF BeauSans Pro';
const FONT_BODY = 'Sarabun';

const FONT = {
  title:      { name: FONT_HEAD, size: 45, bold: true,  color: BRAND.red       },
  subtitle:   { name: FONT_BODY, size: 18, bold: false, color: BRAND.black     },
  body:       { name: FONT_BODY, size: 18, bold: false, color: BRAND.black     },
  shapeLabel: { name: FONT_HEAD, size: 18, bold: true,  color: BRAND.white     },
  coverMain:  { name: FONT_HEAD, size: 44, bold: false, color: BRAND.white     },
  section:    { name: FONT_HEAD, size: 48, bold: true,  color: BRAND.white     },
  closing:    { name: FONT_HEAD, size: 51, bold: false, color: BRAND.redAccent },
  footerUrl:  { name: FONT_BODY, size: 21, bold: false, color: BRAND.gray3     },
};

// ── DIMENSIONS ────────────────────────────────────────────────────────────
// Slide: 1440×810pt = 20"×11.25"
const SLIDE = { w: 20, h: 11.25, margin: 0.5 };

// Footer (extracted from BM04 template — do not change):
const FOOTER = {
  barY: 10.259, barH: 0.991,                    // background strip
  logoX: 17.22, logoY: 10.435, logoW: 1.847, logoH: 0.745,   // white logo
  urlX: 0.549,  urlY: 10.477, urlW: 8.681, urlH: 0.454,       // website text
};

// ── addFooter — call LAST on every slide ─────────────────────────────────
function addFooter(slide) {
  // 1. Footer background bar (gray left + red right — baked into PNG)
  slide.addImage({
    data: 'image/png;base64,' + FOOTER_BAR_B64,
    x: 0, y: FOOTER.barY, w: SLIDE.w, h: FOOTER.barH,
    sizing: { type: 'stretch' },
  });
  // 2. White Viettel Software logo on the red zone
  slide.addImage({
    data: 'image/png;base64,' + LOGO_WHITE_B64,
    x: FOOTER.logoX, y: FOOTER.logoY,
    w: FOOTER.logoW, h: FOOTER.logoH,
    sizing: { type: 'contain', align: 'center', valign: 'middle' },
  });
  // 3. Website URL
  slide.addText('www.viettel.com.vn', {
    x: FOOTER.urlX, y: FOOTER.urlY, w: FOOTER.urlW, h: FOOTER.urlH,
    ...FONT.footerUrl, align: 'left',
  });
}

// ── addBackground — call FIRST on a slide (optional, content slides only) ──
// Variants: 'none' | 'corner-tr' | 'corner-bl' | 'dual-corners' |
//           'side-arc-left' | 'red-watermark'
// Rule: never use on cover or section divider. Footer is rendered last and
// overlays the background — never reverse the order.
function addBackground(slide, variant = 'corner-tr') {
  if (variant === 'none') return;

  // Helper: pale ellipse, sits behind everything.
  const pale = (opts) => slide.addShape('ellipse', {
    fill: { color: BRAND.gray4 },        // #E6E6E6 — safest pale
    line: { type: 'none' },
    ...opts,
  });

  // Helper: red watermark ellipse, very transparent.
  const redMark = (opts) => slide.addShape('ellipse', {
    fill: { color: BRAND.red, transparency: 92 },  // 92% transparent = 8% visible
    line: { type: 'none' },
    ...opts,
  });

  if (variant === 'corner-tr') {
    // One pale circle peeking from top-right corner.
    pale({ x: 17.0, y: -2.5, w: 6.0, h: 6.0 });

  } else if (variant === 'corner-bl') {
    // One pale circle peeking from bottom-left, above the footer.
    pale({ x: -2.5, y: 7.0, w: 5.5, h: 5.5 });

  } else if (variant === 'dual-corners') {
    // Two opposite pale circles — gives slight diagonal balance.
    pale({ x: 17.5, y: -2.0, w: 5.0, h: 5.0 });
    pale({ x: -2.0, y: 6.8, w: 4.5, h: 4.5 });

  } else if (variant === 'side-arc-left') {
    // Large pale circle whose right edge serves as a vertical arc on left side.
    // Most of it is off-canvas to the left — only the right edge shows.
    pale({ x: -8.0, y: 1.0, w: 9.0, h: 9.0 });

  } else if (variant === 'red-watermark') {
    // Big red watermark ellipse, very faint — accent for important slides.
    redMark({ x: 14.0, y: -3.0, w: 9.0, h: 9.0 });

  } else {
    throw new Error(`Unknown background variant: ${variant}`);
  }
}
```

---

## Background Usage Pattern

```javascript
// Order on every content slide:
//   1. addBackground(slide, variant)   ← optional, FIRST
//   2. ... title, subtitle, content ...
//   3. addFooter(slide)                ← always LAST

function addContentSlide(pptx, { title, subtitle, bgVariant = 'corner-tr' }) {
  const slide = pptx.addSlide();
  addBackground(slide, bgVariant);              // 1. behind everything

  slide.addText(title.toUpperCase(), {           // 2. content
    x: 0.5, y: 0.502, w: 19, h: 0.9,
    ...FONT.title, align: 'center', valign: 'middle',
  });
  slide.addText(subtitle, {
    x: 0.5, y: 1.292, w: 19, h: 0.6,
    ...FONT.subtitle, align: 'center', valign: 'middle',
  });
  // ... add shapes / diagrams / icons here ...

  addFooter(slide);                              // 3. on top
  return slide;
}
```

### Variant Selection Rule of Thumb

| Loại slide | Variant đề xuất |
|---|---|
| Slide đầu của một chương | `'red-watermark'` |
| Slide nội dung text bình thường (bullet, list) | `'corner-tr'` |
| Slide có heading mạnh, ít text | `'corner-bl'` |
| Slide ít nội dung, cần "đỡ" bố cục | `'dual-corners'` |
| Slide có list/timeline dọc bên trái | `'side-arc-left'` |
| Diagram dense, Venn, chevron, process flow | `'none'` |
| Cover, Section Divider, Closing | **không gọi `addBackground`** |

### Anti-patterns (đã tránh trong helper)

- Shape decorative đặt trong vùng `x: 2"–18", y: 1.5"–9.5"` → che text
- Opacity dưới 85 → quá đậm, lấn nội dung
- Dùng màu ngoài bảng cho phép (vd `#5A5A5A`, `#808080` cho background) → trông như shape nội dung bị lạc
- Quên gọi `addFooter` sau `addBackground` → footer bị che
- Dùng background trên cover/section divider → đè lên photo full-bleed

---

## Cover Slide Code Pattern

```javascript
function addCoverSlide(pptx, { bgUrl, category, title }) {
  const slide = pptx.addSlide();
  const bgB64 = fetchImageAsBase64(bgUrl, '/tmp/cover_bg.jpg');

  // Background photo
  slide.addImage({ data: 'image/jpeg;base64,' + bgB64,
    x: 0, y: 0, w: SLIDE.w, h: SLIDE.h,
    sizing: { type: 'cover', align: 'center', valign: 'middle' } });

  // Category pill + label
  slide.addImage({ data: 'image/png;base64,' + COVER_SUB_B64,
    x: 0, y: 4.306, w: 6.216, h: 1.024, sizing: { type: 'stretch' } });
  slide.addText(category.toUpperCase(), {
    x: 0.2, y: 4.518, w: 6.0, h: 0.64,
    name: FONT_HEAD, size: 20, color: BRAND.redAccent, align: 'left', valign: 'middle' });

  // Title pill + main title
  slide.addImage({ data: 'image/png;base64,' + COVER_PILL_B64,
    x: 1.209, y: 5.625, w: 7.361, h: 1.706, sizing: { type: 'stretch' } });
  slide.addText(title.toUpperCase(), {
    x: 1.621, y: 6.007, w: 6.536, h: 0.841,
    ...FONT.coverMain, align: 'center', valign: 'middle' });

  addFooter(slide);
  return slide;
}
```

## Section Divider Code Pattern

```javascript
function addSectionSlide(pptx, { photoUrl, title }) {
  const slide = pptx.addSlide();
  const photoB64 = fetchImageAsBase64(photoUrl, '/tmp/section.jpg');

  // Photo left panel
  slide.addImage({ data: 'image/jpeg;base64,' + photoB64,
    x: 0, y: 0, w: 9.194, h: 10.072,
    sizing: { type: 'cover', align: 'center', valign: 'middle' } });

  // Red blob
  slide.addImage({ data: 'image/png;base64,' + SECTION_BLOB_B64,
    x: 7.446, y: 2.601, w: 7.575, h: 4.858, sizing: { type: 'stretch' } });

  // Section title on blob
  slide.addText(title, {
    x: 8.861, y: 3.452, w: 4.661, h: 3.063,
    ...FONT.section, align: 'center', valign: 'middle' });

  addFooter(slide);
  return slide;
}
```

## Section Divider — Geometric Bold (Alternative, no photos required)

Use these variants when photos are unavailable or you want a bolder, graphic-only look.
They rely on custGeom freeform shapes and ellipses via `edit_slide_xml` OOXML — no image assets needed (except footer).

**General rules:**

- Section number: 60pt PF BeauSans Pro Bold, white @30% alpha (on colored background) or 24pt #EE1A2E (on white background)
- Title: PF BeauSans Pro Light Bold, ALL CAPS, 30–36pt
- Subtitle/description: Sarabun Regular, 14–16pt, #5A5A5A
- Footer bar is always rendered last (same `addFooter()` call)
- Use a different variant for each section within the same deck for visual variety
- Number sections sequentially: "01", "02", "03"

All coordinates use EMU (1pt = 12700 EMU).
Standard slide: **12192000 × 6858000 EMU** (960×540pt). Footer bar at y=6248400 EMU.
For 1440×810pt slides (18288000 × 10287000 EMU): multiply all x, y, cx, cy by **1.5**. Font sizes (`sz`) stay unchanged.

| Slide size | Scale factor | Footer Y (EMU) |
|---|---|---|
| 960×540pt (12192000×6858000) | 1.0× | 6248400 |
| 1440×810pt (18288000×10287000) | 1.5× | 9372600 |

### Variant A — Diagonal Split

Left ~69% red diagonal fill with a thin gray accent stripe along the edge and a pale gray triangle in the top-right corner. Title white on red (left-aligned), description on white area (right side).

| # | Shape | Type | Fill | xfrm (EMU) | Notes |
|---|---|---|---|---|---|
| 1 | RedDiagonal | custGeom | #EE1A2E | x=0, y=0, cx=12192000, cy=6248400 | path: moveTo(0,0)→lnTo(8382000,0)→lnTo(7112000,6248400)→lnTo(0,6248400)→close |
| 2 | GrayStripe | custGeom | #5A5A5A | x=0, y=0, cx=12192000, cy=6248400 | path: moveTo(8382000,0)→lnTo(8636000,0)→lnTo(7366000,6248400)→lnTo(7112000,6248400)→close |
| 3 | GrayTriangle | custGeom | #E6E6E6 | x=0, y=0, cx=12192000, cy=6248400 | path: moveTo(8890000,0)→lnTo(12192000,0)→lnTo(12192000,2540000)→close |
| 4 | SectionNum | rect, noFill | — | x=762000, y=635000, cx=2540000, cy=1016000 | "01", 60pt PF BeauSans Pro Bold, white @30% alpha |
| 5 | SectionTitle | rect, noFill | — | x=762000, y=1778000, cx=5334000, cy=1524000 | 32pt PF BeauSans Pro Light Bold, white, algn="l" |
| 6 | AccentLine | cxnSp, line | #FFFFFF, 2pt/25400 | x=762000, y=3429000, cx=1524000, cy=0 | White horizontal accent line under title |
| 7 | SectionDesc | rect, noFill | — | x=8128000, y=2540000, cx=3556000, cy=1524000 | 14pt Sarabun, #5A5A5A, algn="ctr", bodyPr anchor="ctr" |

**Variant A — Full OOXML template (inject into spTree via edit_slide_xml):**

```xml
<!-- 1. RedDiagonal — left ~69% red with diagonal cut -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:nvSpPr>
    <p:cNvPr id="10" name="RedDiagonal"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6248400"/></a:xfrm>
    <a:custGeom>
      <a:avLst/>
      <a:gdLst/>
      <a:ahLst/>
      <a:cxnLst/>
      <a:rect l="l" t="t" r="r" b="b"/>
      <a:pathLst>
        <a:path w="12192000" h="6248400">
          <a:moveTo><a:pt x="0" y="0"/></a:moveTo>
          <a:lnTo><a:pt x="8382000" y="0"/></a:lnTo>
          <a:lnTo><a:pt x="7112000" y="6248400"/></a:lnTo>
          <a:lnTo><a:pt x="0" y="6248400"/></a:lnTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
    <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p><a:endParaRPr lang="en-US"/></a:p>
  </p:txBody>
</p:sp>

<!-- 2. GrayStripe — thin diagonal accent along red edge -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:nvSpPr>
    <p:cNvPr id="11" name="GrayStripe"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6248400"/></a:xfrm>
    <a:custGeom>
      <a:avLst/>
      <a:gdLst/>
      <a:ahLst/>
      <a:cxnLst/>
      <a:rect l="l" t="t" r="r" b="b"/>
      <a:pathLst>
        <a:path w="12192000" h="6248400">
          <a:moveTo><a:pt x="8382000" y="0"/></a:moveTo>
          <a:lnTo><a:pt x="8636000" y="0"/></a:lnTo>
          <a:lnTo><a:pt x="7366000" y="6248400"/></a:lnTo>
          <a:lnTo><a:pt x="7112000" y="6248400"/></a:lnTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
    <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p><a:endParaRPr lang="en-US"/></a:p>
  </p:txBody>
</p:sp>

<!-- 3. GrayTriangle — pale gray in top-right corner -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="12" name="GrayTriangle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6248400"/></a:xfrm>
    <a:custGeom>
      <a:avLst/>
      <a:gdLst/>
      <a:ahLst/>
      <a:cxnLst/>
      <a:rect l="l" t="t" r="r" b="b"/>
      <a:pathLst>
        <a:path w="12192000" h="6248400">
          <a:moveTo><a:pt x="8890000" y="0"/></a:moveTo>
          <a:lnTo><a:pt x="12192000" y="0"/></a:lnTo>
          <a:lnTo><a:pt x="12192000" y="2540000"/></a:lnTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
    <a:solidFill><a:srgbClr val="E6E6E6"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p><a:endParaRPr lang="en-US"/></a:p>
  </p:txBody>
</p:sp>

<!-- 4. SectionNum -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="13" name="SectionNum"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="635000"/><a:ext cx="2540000" cy="1016000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="6000" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"><a:alpha val="30000"/></a:srgbClr></a:solidFill>
          <a:latin typeface="PF BeauSans Pro"/>
        </a:rPr>
        <a:t>01</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 5. SectionTitle -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="14" name="SectionTitle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="1778000"/><a:ext cx="5334000" cy="1524000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="t" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="3200" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
          <a:latin typeface="PF BeauSans Pro Light"/>
        </a:rPr>
        <a:t>SECTION TITLE
LINE TWO</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 6. AccentLine — white 2pt line under title -->
<p:cxnSp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
         xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvCxnSpPr>
    <p:cNvPr id="15" name="AccentLine"/>
    <p:cNvCxnSpPr/>
    <p:nvPr/>
  </p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="3429000"/><a:ext cx="1524000" cy="0"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="25400">
      <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
    </a:ln>
  </p:spPr>
</p:cxnSp>

<!-- 7. SectionDesc — on white area, right side -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="16" name="SectionDesc"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="8128000" y="2540000"/><a:ext cx="3556000" cy="1524000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="ctr"/>
      <a:r>
        <a:rPr lang="en-US" sz="1400" dirty="0">
          <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
          <a:latin typeface="Sarabun"/>
        </a:rPr>
        <a:t>Section description here</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### Variant B — Angled Band

A full-width red band with angled edges across the middle of the slide.

| # | Shape | Type | Fill | xfrm (EMU) | Notes |
|---|---|---|---|---|---|
| 1 | RedBand | custGeom | #EE1A2E | x=0, y=1524000, cx=12192000, cy=3810000 | path: moveTo(0,635000)→lnTo(12192000,0)→lnTo(12192000,3175000)→lnTo(0,3810000)→close |
| 2 | GrayBar | custGeom | #5A5A5A | x=0, y=1371600, cx=12192000, cy=762000 | path: moveTo(0,508000)→lnTo(12192000,0)→lnTo(12192000,190500)→lnTo(0,698500)→close |
| 3 | SectionNum | rect, noFill | — | x=762000, y=2032000, cx=2540000, cy=1016000 | "02", 60pt PF BeauSans Pro Bold, white @30% alpha |
| 4 | SectionTitle | rect, noFill | — | x=762000, y=2794000, cx=10668000, cy=1143000 | 36pt PF BeauSans Pro Light Bold, white, algn="ctr" |
| 5 | SectionDesc | rect, noFill | — | x=762000, y=5461000, cx=10668000, cy=508000 | 16pt Sarabun, #5A5A5A, algn="ctr" |
| 6 | Dot1 | ellipse | #E6E6E6 | x=10668000, y=5842000, cx=203200, cy=203200 | Decorative dot |
| 7 | Dot2 | ellipse | #B4B4B4 | x=11049000, y=5842000, cx=203200, cy=203200 | Decorative dot |
| 8 | Dot3 | ellipse | #EE1A2E | x=11430000, y=5842000, cx=203200, cy=203200 | Decorative dot (active) |

**Variant B — Full OOXML template (inject into spTree via edit_slide_xml):**

```xml
<!-- 1. RedBand — angled red trapezoid -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:nvSpPr>
    <p:cNvPr id="10" name="RedBand"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="1524000"/><a:ext cx="12192000" cy="3810000"/></a:xfrm>
    <a:custGeom>
      <a:avLst/>
      <a:gdLst/>
      <a:ahLst/>
      <a:cxnLst/>
      <a:rect l="l" t="t" r="r" b="b"/>
      <a:pathLst>
        <a:path w="12192000" h="3810000">
          <a:moveTo><a:pt x="0" y="635000"/></a:moveTo>
          <a:lnTo><a:pt x="12192000" y="0"/></a:lnTo>
          <a:lnTo><a:pt x="12192000" y="3175000"/></a:lnTo>
          <a:lnTo><a:pt x="0" y="3810000"/></a:lnTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
    <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p><a:endParaRPr lang="en-US"/></a:p>
  </p:txBody>
</p:sp>

<!-- 2. GrayBar — angled gray accent bar -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:nvSpPr>
    <p:cNvPr id="11" name="GrayBar"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="1371600"/><a:ext cx="12192000" cy="762000"/></a:xfrm>
    <a:custGeom>
      <a:avLst/>
      <a:gdLst/>
      <a:ahLst/>
      <a:cxnLst/>
      <a:rect l="l" t="t" r="r" b="b"/>
      <a:pathLst>
        <a:path w="12192000" h="762000">
          <a:moveTo><a:pt x="0" y="508000"/></a:moveTo>
          <a:lnTo><a:pt x="12192000" y="0"/></a:lnTo>
          <a:lnTo><a:pt x="12192000" y="190500"/></a:lnTo>
          <a:lnTo><a:pt x="0" y="698500"/></a:lnTo>
          <a:close/>
        </a:path>
      </a:pathLst>
    </a:custGeom>
    <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:p><a:endParaRPr lang="en-US"/></a:p>
  </p:txBody>
</p:sp>

<!-- 3. SectionNum -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="12" name="SectionNum"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="2032000"/><a:ext cx="2540000" cy="1016000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="6000" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"><a:alpha val="30000"/></a:srgbClr></a:solidFill>
          <a:latin typeface="PF BeauSans Pro"/>
        </a:rPr>
        <a:t>02</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 4. SectionTitle -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="13" name="SectionTitle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="2794000"/><a:ext cx="10668000" cy="1143000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="ctr"/>
      <a:r>
        <a:rPr lang="en-US" sz="3600" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
          <a:latin typeface="PF BeauSans Pro Light"/>
        </a:rPr>
        <a:t>SECTION TITLE HERE</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 5. SectionDesc -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="14" name="SectionDesc"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="762000" y="5461000"/><a:ext cx="10668000" cy="508000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="ctr" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="ctr"/>
      <a:r>
        <a:rPr lang="en-US" sz="1600" dirty="0">
          <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
          <a:latin typeface="Sarabun"/>
        </a:rPr>
        <a:t>Section description here</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 6–8. Decorative dots -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr><p:cNvPr id="15" name="Dot1"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="10668000" y="5842000"/><a:ext cx="203200" cy="203200"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="E6E6E6"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr><p:cNvPr id="16" name="Dot2"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="11049000" y="5842000"/><a:ext cx="203200" cy="203200"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="B4B4B4"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr><p:cNvPr id="17" name="Dot3"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="11430000" y="5842000"/><a:ext cx="203200" cy="203200"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>
```

### Variant C — Circle Overlay

Two large circles overlapping on the right (intentionally overflowing the slide edge for bold effect); content on the left.

| # | Shape | Type | Fill | xfrm (EMU) | Notes |
|---|---|---|---|---|---|
| 1 | RedCircle | ellipse | #EE1A2E | x=6858000, y=254000, cx=5588000, cy=5588000 | Intentionally overflows right edge ~20pt |
| 2 | GrayCircle | ellipse | #5A5A5A | x=8382000, y=1778000, cx=4445000, cy=4445000 | Overflows right ~50pt, overlaps RedCircle |
| 3 | SmallCircle | ellipse | #E6E6E6 | x=6350000, y=4318000, cx=1016000, cy=1016000 | Decorative accent |
| 4 | VertAccent | rect | #EE1A2E | x=635000, y=2159000, cx=76200, cy=1651000 | Thin red vertical bar |
| 5 | SectionNum | rect, noFill | — | x=914400, y=1651000, cx=2540000, cy=635000 | "03", 24pt PF BeauSans Pro Bold, #EE1A2E, anchor="b" |
| 6 | SectionTitle | rect, noFill | — | x=914400, y=2349500, cx=5334000, cy=1524000 | 2-line, 30pt PF BeauSans Pro Light Bold, #000000 |
| 7 | AccentLine | cxnSp, line | #B4B4B4, 1.5pt | x=914400, y=3937000, cx=1016000, cy=0 | Horizontal accent line |
| 8 | SectionDesc | rect, noFill | — | x=914400, y=4064000, cx=5080000, cy=762000 | 14pt Sarabun, #5A5A5A, anchor="t" |

**Variant C — Full OOXML template (inject into spTree via edit_slide_xml):**

```xml
<!-- 1. RedCircle — large red, overflows right -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="10" name="RedCircle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="6858000" y="254000"/><a:ext cx="5588000" cy="5588000"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>

<!-- 2. GrayCircle — overlaps RedCircle, overflows right -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="11" name="GrayCircle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="8382000" y="1778000"/><a:ext cx="4445000" cy="4445000"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>

<!-- 3. SmallCircle — decorative -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="12" name="SmallCircle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="6350000" y="4318000"/><a:ext cx="1016000" cy="1016000"/></a:xfrm>
    <a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="E6E6E6"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>

<!-- 4. VertAccent — thin red vertical bar -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="13" name="VertAccent"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="635000" y="2159000"/><a:ext cx="76200" cy="1651000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>
</p:sp>

<!-- 5. SectionNum -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="14" name="SectionNum"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="914400" y="1651000"/><a:ext cx="2540000" cy="635000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="b" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="2400" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="EE1A2E"/></a:solidFill>
          <a:latin typeface="PF BeauSans Pro"/>
        </a:rPr>
        <a:t>03</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 6. SectionTitle -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="15" name="SectionTitle"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="914400" y="2349500"/><a:ext cx="5334000" cy="1524000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="t" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="3000" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="000000"/></a:solidFill>
          <a:latin typeface="PF BeauSans Pro Light"/>
        </a:rPr>
        <a:t>SECTION TITLE
LINE TWO</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>

<!-- 7. AccentLine — horizontal gray line -->
<p:cxnSp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
         xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvCxnSpPr>
    <p:cNvPr id="16" name="AccentLine"/>
    <p:cNvCxnSpPr/>
    <p:nvPr/>
  </p:nvCxnSpPr>
  <p:spPr>
    <a:xfrm><a:off x="914400" y="3937000"/><a:ext cx="1016000" cy="0"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="19050">
      <a:solidFill><a:srgbClr val="B4B4B4"/></a:solidFill>
    </a:ln>
  </p:spPr>
</p:cxnSp>

<!-- 8. SectionDesc -->
<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:nvSpPr>
    <p:cNvPr id="17" name="SectionDesc"/>
    <p:cNvSpPr/>
    <p:nvPr/>
  </p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="914400" y="4064000"/><a:ext cx="5080000" cy="762000"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:noFill/>
    <a:ln><a:noFill/></a:ln>
  </p:spPr>
  <p:txBody>
    <a:bodyPr anchor="t" anchorCtr="0"/>
    <a:lstStyle/>
    <a:p>
      <a:pPr algn="l"/>
      <a:r>
        <a:rPr lang="en-US" sz="1400" dirty="0">
          <a:solidFill><a:srgbClr val="5A5A5A"/></a:solidFill>
          <a:latin typeface="Sarabun"/>
        </a:rPr>
        <a:t>Section description here</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
```

### How to inject Geometric Bold dividers via edit_slide_xml

```javascript
// 1. Read slide XML
const xml = await zip.file("ppt/slides/slide1.xml")?.async("string");
const doc = new DOMParser().parseFromString(xml, "text/xml");
const NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main";
const NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main";
const spTree = doc.getElementsByTagNameNS(NS_P, "spTree")[0];

// 2. Remove old shapes (keep footer shapes with id < 10)
const toRemove = [];
for (let i = 0; i < spTree.childNodes.length; i++) {
  const node = spTree.childNodes[i];
  if (node.nodeType !== 1) continue;
  const cNvPrs = node.getElementsByTagNameNS("*", "cNvPr");
  if (cNvPrs.length > 0) {
    const id = parseInt(cNvPrs[0].getAttribute("id"));
    if (id >= 10) toRemove.push(node);
  }
}
toRemove.forEach(n => n.parentNode.removeChild(n));

// 3. Inject variant shapes from template XML
// Pick the right variant XML string (variantB or variantC)
const shapesXml = `<wrapper
  xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  ${variantShapesHere}
</wrapper>`;
const wrapper = new DOMParser().parseFromString(shapesXml, "text/xml")
  .documentElement;
for (let i = 0; i < wrapper.childNodes.length; i++) {
  if (wrapper.childNodes[i].nodeType === 1) {
    spTree.appendChild(doc.importNode(wrapper.childNodes[i], true));
  }
}

// 4. Replace placeholder text with actual content
// Find shapes by name, replace <a:t> content
const shapes = spTree.getElementsByTagNameNS(NS_P, "sp");
for (const sp of shapes) {
  const cNvPr = sp.getElementsByTagNameNS("*", "cNvPr")[0];
  const name = cNvPr?.getAttribute("name");
  if (name === "SectionNum") {
    sp.getElementsByTagNameNS(NS_A, "t")[0].textContent = "02";
  } else if (name === "SectionTitle") {
    sp.getElementsByTagNameNS(NS_A, "t")[0].textContent = "YOUR TITLE";
  } else if (name === "SectionDesc") {
    sp.getElementsByTagNameNS(NS_A, "t")[0].textContent = "Your description";
  }
}

// 5. Write back
zip.file("ppt/slides/slide1.xml",
  new XMLSerializer().serializeToString(doc));
markDirty();
```

### Important notes for Geometric Bold dividers

1. All XML above has been tested and verified in actual PowerPoint
2. Namespace declarations (`xmlns:p`, `xmlns:a`) are required when parsing with DOMParser
3. Circles in Variant C intentionally overflow the slide edge for a bold visual effect — this is by design, not a bug
4. Shape IDs must be unique within a slide — when injecting, verify IDs don't conflict with existing shapes
5. Footer shapes (`footer_bar.png`, `logo_white.png`, URL text) must always be preserved — never modify them
6. Each variant includes complete OOXML with full `<p:sp>`, `<p:cxnSp>` elements, namespaces, `txBody`, and `spPr`
7. When creating a new section divider, copy the entire XML block for the chosen variant and only replace: section number, title text, and description text

## Image Fetch Helper

```javascript
function fetchImageAsBase64(url, localPath) {
  const { execSync } = require('child_process');
  const fs = require('fs');
  execSync(`curl -sL "${url}" -o "${localPath}"`);
  return fs.readFileSync(localPath).toString('base64');
}
```

---

## Image Sourcing

| Loại slide | Cần ảnh? | Vị trí |
|---|---|---|
| Cover | **Bắt buộc** | Full-bleed background |
| Section Divider (photo) | **Bắt buộc** | Left panel 9.194" wide |
| Section Divider (Geometric Bold) | Không cần | Variant B/C dùng hình học thay ảnh |
| Content / Diagram | Tuỳ chọn | Góc phải hoặc inline |
| Process / Steps | Không cần | — |
| Closing | Khuyến nghị | Circular crop right side |

Dùng `image_search` tool với từ khoá tiếng Anh 3–5 từ cụ thể, chuyên nghiệp.
Luôn dùng overlay tối (40–50% opacity đen) khi đặt text lên ảnh sáng.

---

## Animations & Transitions

```javascript
// Per-slide transition
slide.transition = { type: 'fade', dur: 600 };    // content slides
slide.transition = { type: 'push', dur: 600 };    // into section dividers
slide.transition = { type: 'zoom', dur: 1000 };   // closing slide only
```

```javascript
// Element animations
// Title: fade in
slide.addText(title, { ...FONT.title,
  animate: { type: 'fade', trigger: 'afterPrev', dur: 400 } });

// Steps: click through
slide.addShape(..., { animate: { type: 'fly', trigger: 'onClick', dur: 400 } });
```

Rules: max 2 transition types per deck; dur ≤ 600ms for regular elements;
no bounce/spin/spiral; never animate the footer.

---

## Slide Master Theme (Production Settings)

When creating a new deck, set up the master theme with these **exact** values via `edit_slide_master`. These are extracted from the current production template and must match 100%.

### Theme Colors (`a:clrScheme`)

| Slot | Hex | Role |
|---|---|---|
| dk1 | `#000000` | Primary text |
| dk2 | `#42494D` | Theme-only (do NOT use as direct shape fill) |
| lt1 | `#FFFFFF` | Primary background |
| lt2 | `#F3F3F4` | Footer bar left panel bg |
| accent1 | `#EE1A2E` | Primary red — titles, primary shapes |
| accent2 | `#5A5A5A` | Dark gray fills |
| accent3 | `#808080` | Mid gray fills |
| accent4 | `#B4B4B4` | Light gray, footer URL text |
| accent5 | `#E6E6E6` | Pale gray fills, decorative |
| accent6 | `#EE0033` | Accent red — cover label, closing title |
| hlink | `#EE1A2E` | Hyperlink color |
| folHlink | `#808080` | Followed hyperlink color |

### Theme Fonts

| Role | Font |
|---|---|
| Major (titles) | PF BeauSans Pro Light |
| Minor (body) | Sarabun |

### Master Background & Text Styles

- Master background: `#FFFFFF` solid fill
- Title `txStyle` color: `#EE1A2E`
- Body `txStyle` color: `#000000`

### Master Shapes (Default Placeholders)

| id | Name | x | y | cx | cy |
|---|---|---|---|---|---|
| 2 | Title Placeholder 1 | 838200 | 365125 | 10515600 | 1325563 |
| 3 | Text Placeholder 2 | 838200 | 1825625 | 10515600 | 4351338 |
| 4 | Date Placeholder 3 | 838200 | 6356350 | 2743200 | 365125 |
| 5 | Footer Placeholder 4 | 4038600 | 6356350 | 4114800 | 365125 |
| 6 | Slide Number Placeholder 5 | 8610600 | 6356350 | 2743200 | 365125 |

Layout count: 12 layouts available.

### Important Master Theme Rules

- `clrScheme` must match 100% — all dk/lt/accent slots as listed above
- Font scheme: PF BeauSans Pro Light (major) / Sarabun (minor) — no substitutions; install the bundled fonts from `assets/fonts/` on the rendering machine
- Master bg: `#FFFFFF` — never change
- txStyles: title = `#EE1A2E`, body = `#000000`
- Do NOT add decorative shapes to master — use `footer_bar.png` assets on each slide instead
- `dk2` (`#42494D`) exists only in theme XML — never use it as a direct shape fill color

---

## QA Checklist (Brand-Specific)

- [ ] `addFooter()` called last on every slide
- [ ] `footer_bar.png` used — not drawn shapes
- [ ] No content below y=10.0"
- [ ] All titles: ALL CAPS, 45pt Bold, `#EE1A2E`, centered
- [ ] Shape fills: only `#EE1A2E`, `#5A5A5A`, `#808080`, `#E6E6E6`
- [ ] White text only on dark/red fills
- [ ] Footer URL is `#B4B4B4` (not white)
- [ ] Cover has full-bleed photo + pill assets (not shapes)
- [ ] Section divider uses `section_blob.png` (not drawn circle)
- [ ] Vietnamese characters render correctly
- [ ] Max 2 transition types per deck
- [ ] No animation bounce/spin/spiral/random
- [ ] Master theme clrScheme matches all 12 slots exactly
- [ ] Font scheme: PF BeauSans Pro Light (major) / Sarabun (minor)
- [ ] Heading text uses `PF BeauSans Pro`; body text uses `Sarabun` (no Calibri fallbacks)
- [ ] Bundled fonts in `assets/fonts/` are installed on the rendering system
- [ ] Master txStyles: title=`#EE1A2E`, body=`#000000`
- [ ] No decorative shapes in slide master (footer via assets only)
- [ ] If `addBackground()` used: called FIRST (before content), `addFooter()` still last
- [ ] Background shapes only at corners/edges, never in central content area (`x: 2"–18", y: 1.5"–9.5"`)
- [ ] Background colors restricted to: `#E6E6E6`, `#B4B4B4`, or red with `transparency ≥ 92`
- [ ] No background on cover, section divider, or closing slides
- [ ] Max 2 decorative shapes per slide

---

## Common Mistakes

- ❌ Drawing the footer bar as shapes — use `footer_bar.png`
- ❌ Using `Calibri`, `Arial`, or other fallbacks — headings must be `PF BeauSans Pro`, body must be `Sarabun`
- ❌ Generating a deck without first installing the fonts in `assets/fonts/` on the rendering machine — PowerPoint will silently substitute
- ❌ Using `#E80500` or `#42494D` as fill (theme-only values)
- ❌ Wrong red: titles/shapes use `#EE1A2E`; cover label/closing use `#EE0033`
- ❌ Footer URL as white text (background is light gray `#F3F3F4` — use `#B4B4B4`)
- ❌ Footer height 40pt — correct is **71pt / 0.991"**
- ❌ Drawing cover pills/section blob as shapes — use the PNG assets
- ❌ Lowercase slide titles
- ❌ Body text below 14pt
- ❌ More than 3 accent colors per slide
- ❌ Deck without photos — covers and photo-style section dividers must have real photos (Geometric Bold dividers are the exception)
- ❌ Text directly on photo without overlay
- ❌ Background decorative shape đặt giữa slide (đè text) — chỉ dùng góc/cạnh
- ❌ Background shape dùng `#5A5A5A` hoặc `#808080` (màu content) — chỉ pale `#E6E6E6` hoặc red mờ ≥92%
- ❌ Gọi `addBackground` SAU content → đè lên text; phải gọi đầu tiên
- ❌ Dùng background trên cover/section divider → đè ảnh full-bleed
- ❌ Nhiều hơn 2 shape decorative trên một slide → rối mắt

---

## Workflow Summary

1. Read `/mnt/skills/public/pptx/SKILL.md` (tooling, PptxGenJS, QA loop)
2. Set up master theme via `edit_slide_master` — clrScheme, fonts, txStyles (see "Slide Master Theme" section)
3. Copy BRAND + FONT + SLIDE + FOOTER constants above into your script
4. `loadB64()` all 5 asset PNGs at top of script
5. Xác định slide nào cần ảnh → `image_search` → `fetchImageAsBase64`
6. (Tùy chọn) Với content slide, chọn variant background phù hợp → gọi `addBackground(slide, variant)` **ngay sau** khi tạo slide
7. Build mỗi slide theo template, gọi `addFooter(slide)` **cuối cùng** trên mọi slide
8. Gắn `slide.transition` cho từng slide
9. Chạy QA: `markitdown`, convert to images, visual inspect, fix, re-verify
