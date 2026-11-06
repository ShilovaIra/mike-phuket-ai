---
name: Mike Phuket AI
description: Daylight Mini App with Mike in the frame, and a violet glass desk for operators.
colors:
  guide-blue: "#2F7CF6"
  guide-blue-hover: "#3B86F7"
  guide-blue-press: "#1F66D6"
  lobby-violet: "#6D4DFF"
  lobby-violet-hot: "#7D62FF"
  plate-yellow: "#FDCB1A"
  harbor-navy: "#0C2E5F"
  harbor-deep: "#042048"
  canvas: "#F4F7FB"
  surface: "#FFFFFF"
  ink: "#102033"
  ink-muted: "#3D5270"
  line: "#D5DEEA"
  hover: "#EEF3F9"
  wash: "#D9E6F5"
  danger: "#D23B3B"
  open: "#0E7A45"
  star: "#C98400"
  voice: "#07111F"
  canvas-dark: "#0E1622"
  surface-dark: "#182433"
  ink-dark: "#E7EEF7"
  ink-muted-dark: "#93A6C0"
  line-dark: "#2C3C52"
  lobby-ink: "#E7F0FB"
  lobby-muted: "#B7C9E2"
  lobby-faint: "#8EABCB"
  lobby-ground: "#0B0E1A"
  lobby-void: "#070B14"
  lobby-rail: "#101426"
  lobby-danger: "#FFB4AE"
  lobby-line: "rgba(198, 220, 255, 0.16)"
typography:
  display:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0"
  label:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: "0"
rounded:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "14px"
  xl: "16px"
  sheet: "20px"
  pane: "22px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  2xl: "32px"
  3xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.guide-blue}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
    height: "52px"
  button-primary-hover:
    backgroundColor: "{colors.guide-blue-hover}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
  button-primary-active:
    backgroundColor: "{colors.guide-blue-press}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
  button-cta:
    backgroundColor: "{colors.guide-blue}"
    textColor: "#FFFFFF"
    rounded: "{rounded.lg}"
    height: "52px"
  button-cta-hover:
    backgroundColor: "{colors.guide-blue-hover}"
    textColor: "#FFFFFF"
    rounded: "{rounded.lg}"
  button-ops:
    backgroundColor: "{colors.lobby-violet}"
    textColor: "#F7FAFF"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "42px"
  button-ops-hover:
    backgroundColor: "{colors.lobby-violet-hot}"
    textColor: "#F7FAFF"
    rounded: "{rounded.lg}"
  button-ghost:
    backgroundColor: "rgba(255, 255, 255, 0.04)"
    textColor: "{colors.lobby-ink}"
    rounded: "{rounded.lg}"
    padding: "0 16px"
    height: "42px"
  chip:
    backgroundColor: "{colors.guide-blue}"
    textColor: "#FFFFFF"
    rounded: "{rounded.pill}"
    padding: "0 12px"
    height: "36px"
  chip-soon:
    backgroundColor: "{colors.plate-yellow}"
    textColor: "{colors.harbor-deep}"
    rounded: "{rounded.xs}"
    padding: "2px 5px 3px"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "44px"
  input-ops:
    backgroundColor: "rgba(5, 10, 22, 0.45)"
    textColor: "{colors.lobby-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
    height: "44px"
---

# Design System: Mike Phuket AI

## Overview

**Creative North Star: "The Island Concierge"**

A tourist on a phone in daylight, Mike's photograph filling the top of the screen, a short Russian greeting in a white bubble. The Mini App is a cool canvas under that frame: Guide Blue for the ask pill, the links, and the tab that is on. Plate Yellow survives only as the small «скоро» sticker. Place photos sit in cards. They do not become the page.

One product, two desks. Tourists get the daylight Mini App, and a dark theme that keeps the same blue when the phone is dark. Operators get the night lobby: blue-black ground, violet blooms, frosted panes, Lobby Violet on the action and on the nav item that is current. The admin does not wear Mike's face or the yellow sticker. The bot keyboard stays Telegram's, packed two-up, and the Mini App does not copy that grid.

The system rejects cringy consumer apps (over-cute copy, mascot spam, emoji walls, gamified fluff), loud travel-agency Telegram spam and hard-sell real-estate brochure tone, and generic flashy SaaS dashboards that prioritize chrome over the task. It also rejects the old white-desk home (yellow plate button, no photograph, two-up topic tiles) and the cyan «Спроси Майка!» night-map phone. Light is the tourist default. Violet glass is the operator desk.

**Key Characteristics:**
- Canvas ground, Guide Blue actions, Plate Yellow only on «скоро»
- Mike's photograph is the home hero; the name is set in Golos Text on the photo
- Ask pill plus a five-tab dock; place cards and chat carry the rest
- Golos Text for every live string; Harbor Navy stays the wordmark ink, not a UI fill
- Mini App flat at rest; admin depth is frosted glass

## Colors

Daylight is a navy-tinted white. The tourist action is Guide Blue. The operator action is Lobby Violet. Plate Yellow is a sticker, not a button.

### Primary
- **Guide Blue** (`#2F7CF6`): the Mini App action. Ask pill, place CTA, send button, active tab, links, map pins, user chat bubbles, and the focus ring. Hover is `#3B86F7`. Press is `#1F66D6`. The dark theme keeps this blue.

### Secondary
- **Lobby Violet** (`#6D4DFF`): the admin action. Ice buttons, the current in-page tab, the rail mark, and the current page in pagination. Hover is `#7D62FF`. The current rail item is a short gradient from `#7C5CFF` to `#6846F0`, same hue, not a second brand color. Violet blooms sit in the ground and the rail. They are atmosphere, not fills for type.

### Tertiary
- **Plate Yellow** (`#FDCB1A`): the PHUKET bar, now only the «скоро» sticker. Type on it is Harbor Deep. It is never a page, a card, a chart, or an admin control.
- **Harbor Navy** (`#0C2E5F`): wordmark ink. It is not a Mini App fill and not an admin button.
- **Harbor Deep** (`#042048`): ink on Plate Yellow.

### Neutral
- **Canvas** (`#F4F7FB`): Mini App page ground in light. Dark theme ground is `#0E1622`.
- **Surface** (`#FFFFFF`): sheets, rows, search, Mike's bubble, incoming chat. Dark theme surface is `#182433`.
- **Ink** (`#102033`): default Mini App text on canvas and surface. Dark theme ink is `#E7EEF7`.
- **Ink Muted** (`#3D5270`): supporting copy, inactive tabs, placeholders. Dark theme muted is `#93A6C0`. Forbidden as the primary body color in light.
- **Line** (`#D5DEEA`): 1px full borders. Dark theme line is `#2C3C52`.
- **Hover** (`#EEF3F9`): light hover on search and filter chips.
- **Wash** (`#D9E6F5`): empty thumbs, partner marks, and cover fallbacks.
- **Open** (`#0E7A45`): the open-now dot beside a place.
- **Star** (`#C98400`): rating figures.
- **Danger** (`#D23B3B`): tourist error text.
- **Voice** (`#07111F`): the voice screen ground, with a Guide Blue glow behind the portrait.

Admin neutrals are a separate night set. **Lobby ground** (`#0B0E1A`) is the desk. **Lobby void** (`#070B14`) is the page behind the blooms. **Lobby rail** (`#101426`) is the sidebar. **Lobby ink** (`#E7F0FB`), **Lobby muted** (`#B7C9E2`), and **Lobby faint** (`#8EABCB`) are the type ramp. **Lobby line** is `rgba(198, 220, 255, 0.16)`. **Lobby danger** (`#FFB4AE`) is the admin error.

### Named Rules
**The Frame Rule.** Mike's photograph is the home hero. Place photographs live in cards and covers. Tropical stock, sunsets, and palms do not become the page ground.

**The Plate Rule.** Plate Yellow is the «скоро» sticker and the wordmark bar. If it is filling a button, a card, or a header, it is wrong. It does not appear on the admin.

**The Two Desks Rule.** Tourists get Canvas and Guide Blue. Operators get the night lobby and Lobby Violet. Do not put the glass desk on the Mini App, and do not put Mike's portrait on the admin.

## Typography

**Display Font:** Golos Text. There is no second display face, and no wordmark file in the repo to set in the header.
**Body Font:** Golos Text (with Segoe UI, system-ui). Cyrillic-first. A ticket at a marina desk, not a Silicon Valley default.
**Label/Mono Font:** Golos Text. No mono unless a booking code shows up later.

**Character:** One family, weight contrast, short Russian lines. Friendly without bounce. Live text is never squeezed past −0.02em.

### Hierarchy
- **Display** (700, 1.75rem / 28px, 1.1, −0.02em): Mike's name on the hero. Admin screen titles use the same size, weight, and tracking at line-height 1.15.
- **Headline** (700, 1.375rem / 22px, −0.02em): the voice-screen status line. Not a section kicker.
- **Title** (700, 1.125rem / 18px, −0.015em): Mini App section headings (Рекомендации, Места, directory titles). Admin pane titles are 1.05rem / 600.
- **Body** (400, 1rem / 16px, 1.45): page text. Place prose is 0.9375rem and wraps at about 42ch. Admin subtitles sit on Lobby muted, max about 62ch.
- **Label** (500, 0.875rem / 14px, 1.35): form labels, meta, text links. Tabs are 0.75rem / 600. The ask pill is 0.9375rem / 700. Sentence case. No tracked all-caps eyebrows.

### Named Rules
**The One Voice Type Rule.** Golos Text carries every live string. Do not pair a tropical display serif or a second geometric sans. Do not set UI in Inter, DM Sans, Plus Jakarta, or system-only once Golos is loaded.

## Layout

The Mini App is one phone column. The hero sits in a 12px inset, 22px radius, at least 320px tall, under the Telegram safe area. Content rows use 16px side insets. Recommendation cards scroll sideways, two visible, snap-aligned. A dock pins the ask pill and five tabs (Главная, Карта, Чат, Избранное, Профиль) above the home indicator. Place detail is a 248px cover with a surface sheet overlapping it by 16px.

The admin is a 248px rail and a stage padded 28px 32px 48px. Broadcasts cap at 1120px, one-time sends at 860px. At 1100px, stat grids drop to two columns. At 980px, interval and form rows stack. At 900px the rail becomes an off-canvas drawer and the stage padding drops to 16px. At 640px, stat grids and roster filters go to one column.

## Elevation & Depth

The Mini App is flat at rest. Depth is a 1px line, a tonal wash, or a photograph. The hero photo and the place cover do the lifting. Shadows that do exist are signals: the focus ring, the open pin halo, the «скоро» sticker's 1px foot, and the voice portrait's blue glow.

The admin is frosted glass. Panes are translucent, blurred 18px, with a 1px ice edge, an inset top highlight, and one offset shadow. Violet blooms in the ground are the only atmosphere. Buttons carry a smaller violet shadow. Nothing else stacks.

Motion on both desks is 180ms `cubic-bezier(0.16, 1, 0.3, 1)` on color, border, and shadow. `prefers-reduced-motion` removes admin transitions and stops the chat typing dots.

### Shadow Vocabulary
- **Rest, Mini App** (`box-shadow: none`): rows, search, place sheet, dock.
- **Focus, Mini App** (`box-shadow: 0 0 0 2px var(--canvas), 0 0 0 4px #2F7CF6`): keyboard focus. The inner ring matches the theme ground.
- **Sticker foot** (`box-shadow: 0 1px 0 rgba(4, 32, 72, 0.16)`): the «скоро» ticket only.
- **Pane** (`box-shadow: 0 18px 40px rgba(2, 6, 16, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.16)`): admin glass.
- **Ice** (`box-shadow: 0 10px 24px rgba(18, 48, 120, 0.35)`): admin primary buttons.
- **Focus, admin** (`outline: 2px solid #9EC0FF; outline-offset: 1px`): glass fields.

### Named Rules
**The Split Depth Rule.** If a Mini App card has a drop shadow, remove it. If an admin pane is a solid opaque card with no blur, it has left the night lobby.

## Shapes

Tourist actions that ask or send are pills. Place CTAs, search, and filters are 14px. Chat bubbles are 16px with a 4px tail on the speaking corner. The «скоро» sticker is a 4px ticket, tilted 8 degrees. The hero and the admin panes are 22px. The place sheet's top corners are 20px. The admin rail item, in-page tab, and field are 12px. Circles are for the voice portrait, icon buttons, the send button, and partner marks.

Borders are a full 1px. No thick side stripe. The hero clips the photograph; the voice portrait clips to a circle.

## Components

### Buttons
- **Shape:** The ask pill is 999px and 52px tall. The place CTA is 14px and 52px tall. The admin ice button is 14px and 42px tall. Do not put Plate Yellow on any of them.
- **Primary (tourist):** Guide Blue, white type, 0.9375rem, weight 700. Label **Спросите Майка о Пхукете**. One per dock. Hover `#3B86F7`. Active `#1F66D6`. Disabled at 45% opacity.
- **Place CTA:** same blue and weight, 14px radius, full width of the sheet.
- **Ops primary:** Lobby Violet, `#F7FAFF` type, 0.9375rem, weight 600, padding 0 16px, ice shadow. Hover `#7D62FF`. Disabled at 45% opacity.
- **Ghost (admin):** 1px `rgba(190, 214, 255, 0.28)`, fill `rgba(255, 255, 255, 0.04)`, Lobby ink, weight 500. Hover fill `rgba(255, 255, 255, 0.09)`.
- **Hover / Focus:** 180ms on color. Mini App focus is the two-ring shadow. No scale bounce.

### Chips
- **Ask chips in chat:** Guide Blue fill, white type, pill, 36px, padding 0 12px, 0.8125rem, weight 600.
- **Ghost chips:** Surface, Ink, 1px Line.
- **«скоро»:** Plate Yellow, Harbor Deep, 4px radius, 0.625rem, weight 700, rotated 8 degrees. It sits on Карта and on rows that are not live. It is a status, not a button.

### Cards / Containers
- **Mini App rows:** 14px, Surface, 1px Line, no shadow. Recommendation thumbs are 4:3, 14px, Wash until a photo arrives. Partner heads are a 56px circular mark plus two lines.
- **Place sheet:** Surface, 20px top radius, overlapping the cover. Stat cells sit on Canvas inside the sheet, 12px radius.
- **Admin pane:** 22px, ice line, glass gradient `linear-gradient(180deg, rgba(176, 206, 255, 0.18), rgba(14, 26, 48, 0.46))`, blur 18px, pane shadow. Padding about 18px 20px. Pane title is an icon plus 1.05rem type, then one muted help line.

### Inputs / Fields
- **Composer:** Surface, pill, 44px, padding 0 14px, 1px Line, Ink text, Ink Muted placeholder. Send is a 44px Guide Blue circle.
- **Search:** 14px, 48px, Surface, 1px Line. Home search is not live.
- **Admin field:** 12px, at least 44px, padding 10px 12px, fill `rgba(5, 10, 22, 0.45)`, Lobby ink, placeholder `#A9BDD6`. Focus outline `#9EC0FF`. Textareas start at 112px. Errors use Lobby danger at 0.875rem.

### Navigation
Mini App: no hamburger and no wordmark bar. Five tabs, 56px, 26px SVG icons, 0.75rem labels. The current tab is Guide Blue. Inactive is Ink Muted. Карта is Ink-quiet (`#8AA0B8`) and does not navigate. Telegram owns the OS chrome.

Admin: a dark left rail, 248px. The brand row says Admin Panel beside a 36px violet mark. Links are 40px, 12px radius, 0.875rem. The current item is the violet gradient pill with white type. Hover on the others is `rgba(255, 255, 255, 0.06)`. Email and Выйти sit at the foot. Below 900px the rail is a drawer opened by Меню. In-page tabs (one-time versus interval) are solid Lobby Violet when current, 12px, 40px.

### Signature: Mike in the frame
The home hero is `assets/hero-mike.jpg`, cover, centered at 35% height, with a navy scrim `linear-gradient(180deg, rgba(6, 28, 44, 0.55), transparent 72%)`. The name and the one-line role sit on the photo. The greeting is a white bubble, 12px radius with a 4px tail, 0.75rem, max 26ch. This photograph is the concierge. Do not replace it with a circular lockup crop, and do not put a second portrait in the header.

### Signature: Voice portrait
On the voice screen only: a 168px circle, `object-position: 32% 36%`, padded by a Guide Blue ring and a soft blue glow, on the Voice ground. It is not the home hero.

### Telegram reply keyboard
Visuals are Telegram's. Rows pack two-up. Ask Mike sits alone on the last row. The Mini App does not repeat that grid or those emoji. Tabs use SVG icons.

## Do's and Don'ts

### Do:
- **Do** keep the Mini App on Canvas with Surface sheets, Guide Blue actions, and Plate Yellow only on «скоро».
- **Do** lead home with Mike's photograph, the name in Golos Text, and the white greeting bubble.
- **Do** pin one ask pill and the five-tab dock. Hit targets stay at least 44px.
- **Do** set live type in Golos Text, 16px body, sentence case, `text-wrap: pretty` on greeting and chat.
- **Do** keep the admin on the night lobby: violet actions, 22px glass panes, no portrait, no Plate Yellow.
- **Do** honor `prefers-reduced-motion` on the admin desk and the chat typing indicator.

### Don't:
- **Don't** build cringy consumer apps: over-cute copy, mascot spam, emoji walls, gamified fluff.
- **Don't** use loud travel-agency spam or a hard-sell real-estate brochure tone.
- **Don't** put the admin night lobby on the Mini App, or Mike's portrait on the admin.
- **Don't** put beach photography, palms, or sunsets behind the UI. The Frame Rule. Place photos stay inside cards and covers.
- **Don't** use cream, sand, beige, or warm-paper page grounds.
- **Don't** use gradient text, glass on the Mini App, thick side-stripe borders, or identical icon-heading-text card grids.
- **Don't** use a tiny uppercase tracked eyebrow above every section.
- **Don't** treat the cyan «Спроси Майка!» night-map phone as the tourist UI. Light is the default. The dark theme keeps Guide Blue on `#0E1622`.
- **Don't** bring back the yellow ask plate or the two-up topic tiles. That home was replaced.
- **Don't** restyle the partner dashboard with this desk. It stays its own surface until it is redesigned.
