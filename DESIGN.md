---
name: Mike Phuket AI
description: Light concierge Mini App and bot for Phuket, with a quiet operator desk.
colors:
  harbor-navy: "#0C2E5F"
  harbor-deep: "#042048"
  plate-yellow: "#FDCB1A"
  canvas: "#F4F7FB"
  surface: "#FFFFFF"
  ink: "#0A1B36"
  ink-muted: "#3D5270"
  line: "#D5DEEA"
  icon-well: "#E7EEF6"
  danger: "#B42318"
typography:
  display:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.015em"
  title:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Golos Text, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: "0"
rounded:
  sm: "8px"
  md: "16px"
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
    backgroundColor: "{colors.plate-yellow}"
    textColor: "{colors.harbor-deep}"
    typography: "{typography.title}"
    rounded: "{rounded.pill}"
    padding: "16px 24px"
    height: "56px"
  button-primary-hover:
    backgroundColor: "#F0C010"
    textColor: "{colors.harbor-deep}"
    rounded: "{rounded.pill}"
  button-primary-active:
    backgroundColor: "#E0B40A"
    textColor: "{colors.harbor-deep}"
    rounded: "{rounded.pill}"
  button-topic:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "12px 10px 14px"
    height: "96px"
  button-topic-hover:
    backgroundColor: "{colors.icon-well}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  button-ops:
    backgroundColor: "{colors.harbor-navy}"
    textColor: "{colors.surface}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "10px 16px"
    height: "40px"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "12px 14px"
    height: "48px"
---

# Design System: Mike Phuket AI

## 1. Overview

**Creative North Star: "The Island Concierge"**

A tourist on a bright Phuket street, Telegram in one hand, sun on the glass. The Mini App is a white desk: readable in daylight, fast to tap, one person on the other side. Mike's face and short Russian copy carry the warmth. Navy type and a single yellow plate do the wayfinding. Tropical photography stays inside that circle, and in marketing. It never becomes wallpaper.

This is one product with two voices. Tourists get Mike: friendly, clear, local. Operators get a quiet desk in the same palette: navy actions, almost no yellow, no character cosplay. The Mini App home maps 1:1 to the bot keyboard (where to eat, beaches, nearby, property, ask Mike). Labels name the action. Personality lives in the portrait and the greeting, not in decoration.

The system rejects cringy consumer apps (over-cute copy, mascot spam, emoji walls, gamified fluff), loud travel-agency Telegram spam and hard-sell real-estate brochure tone, and generic flashy SaaS dashboards that prioritize chrome over task completion. It also rejects the customer's dark "night map" phone mock as the tourist default: we locked **light concierge** instead.

**Key Characteristics:**
- White working surface, harbor-navy ink, yellow used as a plate, not a wash
- Mike's circular portrait is the only photoreal image in the Mini App
- Topic tiles packed 2-up like the bot keyboard; one primary plate button
- Golos Text in a tight rem scale; the wordmark file is display, not a second UI font
- Flat surfaces at rest; motion is press, focus, and state, 150–250ms

## 2. Colors

Daylight desk: navy-tinted off-white, not cream. Accent is the yellow PHUKET plate from the lockup.

### Primary
- **Harbor Navy** (`#0C2E5F`): sampled from the MIKE wordmark fill. Icons, rings, ops primary buttons, focus rings, links. The color of the desk sign, not of the sea.
- **Harbor Deep** (`#042048`): sampled from PHUKET letters on the yellow bar. Body-critical ink when type sits on yellow; TMA header mark; hover-deep for navy buttons.

### Secondary
- **Plate Yellow** (`#FDCB1A`): sampled from the PHUKET bar. The brand object. Primary tourist CTA, selected chips, the outer hairline around Mike's portrait. Never a page background, never a gradient, never a 40% wash.

### Neutral
- **Canvas** (`#F4F7FB`): Mini App and admin page ground. Chroma tilts toward navy (oklch ~0.975 0.006 255), not toward sand.
- **Surface** (`#FFFFFF`): topic rows, fields, admin tables.
- **Ink** (`#0A1B36`): default text on canvas/surface. Contrast ≥15:1 on canvas.
- **Ink Muted** (`#3D5270`): supporting copy only. Contrast ≥7:1 on canvas. Forbidden as primary body color.
- **Line** (`#D5DEEA`): 1px borders. Full border, never a thick side stripe.
- **Icon Well** (`#E7EEF6`): default 40px circle behind a topic emoji; some tiles tint the well toward the topic.

### Named Rules
**The Desk Rule.** The Mini App body is canvas or surface. Tropical photos, sunsets, and palm illustrations do not appear as backgrounds, section fills, or hero wallpaper.

**The Plate Rule.** Plate yellow occupies ≤10% of any tourist screen, and almost 0% of ops screens. If yellow is filling a card, a chart, or a header bar, it is wrong. Put it back on the plate-shaped CTA.

**The Quiet Tools Rule.** Admin and partner dashboards use Harbor Navy for primary actions (replacing the older `#053e7a` approximation). Plate yellow does not appear on ops chrome. Do not ship the dark-navy SaaS sidebar from the sales PDF.

## 3. Typography

**Display Font:** Wordmark file (`wordmark.png`) for brand lockups only. UI never sets a second display face.
**Body Font:** Golos Text (with Segoe UI, system-ui). Cyrillic-first UI sans; a laminated ticket at a marina desk, not a Silicon Valley default.
**Label/Mono Font:** Golos Text. No mono unless we show a booking code later.

**Character:** One family, weight contrast, short Russian lines. Friendly without bounce. Condensed logo letters stay in the PNG; live text is never squeezed below −0.02em.

### Hierarchy
- **Display** (700, 1.75rem / 28px, 1.15): Mike's name under the portrait. Once per home screen.
- **Headline** (700, 1.375rem / 22px, 1.25): Screen titles in admin. Not used as a kicker.
- **Title** (600, 1.125rem / 18px, 1.3): Primary CTA label, chat title.
- **Body** (400, 1rem / 16px, 1.5, max ~45ch in the Mini App): Greeting and supporting sentences.
- **Label** (500, 0.875rem / 14px, 1.35): Field labels, admin table headers, muted meta. Sentence case. No tracked all-caps eyebrows.

### Named Rules
**The One Voice Type Rule.** Golos Text carries every live string. Do not pair a "tropical" display serif or a second geometric sans. Do not set UI in Inter, DM Sans, Plus Jakarta, or system-only once Golos is loaded.

## 4. Elevation

Flat by default. Depth is a 1px Line border and a tonal well, not a drop shadow. Mike's portrait is the exception: a 3px Harbor Navy ring and a 3px Plate Yellow outer hairline, which read as the lockup object, not as a card shadow.

### Shadow Vocabulary
- **Rest** (`box-shadow: none`): rows, fields, admin tables, page ground.
- **Press** (`box-shadow: inset 0 1px 0 rgba(4, 32, 72, 0.12)`): primary plate button `:active` only.
- **Focus** (`box-shadow: 0 0 0 2px #F4F7FB, 0 0 0 4px #0C2E5F`): keyboard focus. Never rely on color fill alone.

### Named Rules
**The Flat-By-Default Rule.** If a topic row has a shadow, remove it. If an admin card is stacked on a card, flatten it to a table or a single surface.

## 5. Components

### Buttons
- **Shape:** Tourist primary is a plate (pill, 999px), 56px tall, matching the PHUKET bar. Ops primary is 8px radius, 40px tall. Do not mix those shapes on one surface.
- **Primary (tourist):** Plate Yellow fill, Harbor Deep text, 16px 24px, weight 700. Hover `#F0C010`. Active `#E0B40A` plus inset press. Disabled 40% opacity, cursor not-allowed.
- **Topic tile:** Surface fill, 16px radius, 96px min height, 12px 10px 14px, hairline Line border. Packed two per row, same order as the bot keyboard. 40px circle with the bot emoji (no SVG, no chevron). Well tint can shift by topic; hover Icon Well fill. Active slightly deeper tint.
- **Ops primary:** Harbor Navy fill, white text. Hover Harbor Deep. This is the replacement for `bg-[#053e7a]`.
- **Hover / Focus:** 180ms `cubic-bezier(0.16, 1, 0.3, 1)`. Focus ring as Elevation. No scale bounce.

### Chips
Unused on home. If a partner type needs a selected state later: Plate Yellow fill, Harbor Deep text, pill, 32px height. Unselected: Line border, Ink text, canvas fill.

### Cards / Containers
- **Corner Style:** 16px for tourist rows; 8px for admin panels.
- **Background:** Surface on Canvas. Never nested cards.
- **Shadow Strategy:** none at rest.
- **Border:** 1px Line, full perimeter.
- **Internal Padding:** 16px tourist, 16–24px admin.

### Inputs / Fields
- **Style:** Surface, 8px radius, 1px Line, 48px height, 12px 14px, Ink text. Placeholder uses Ink Muted (still ≥4.5:1).
- **Focus:** border Harbor Navy, plus the two-ring focus shadow.
- **Error / Disabled:** 1px Danger border and inline error text in Danger. Disabled canvas fill, 50% ink.

### Navigation
Mini App: no hamburger. Compact stacked wordmark in the top bar (52px height), canvas ground, 1px Line on the bottom edge. Telegram owns the OS chrome. Admin: leftover text nav for now; when it grows, a left rail on Canvas with Harbor Navy current-item text, not a dark sidebar.

### Signature: Mike portrait
Circular crop, 168px on home (136px on short viewports). CSS circle clips the lockup's overlapping yellow bar (`object-position: 32% 40%`, image scaled to ~118%). 3px Harbor Navy ring, 3px Plate Yellow outer hairline, 4px gap of canvas between them. This is the only photoreal image in the Mini App. The wordmark file is for headers, not stacked under the face (the full lockup is marketing).

### Signature: Ask-Mike plate
Full-width plate button, sticky above the home-indicator safe area. Label **Спросить Майка**. Verb + object. One per home screen. Topic rows never use yellow fill.

### Telegram reply keyboard (bot)
Visuals are Telegram's. Labels stay short and specific, same nouns as the Mini App. The Mini App reuses the same one emoji per topic inside the circle, packed 2-up. Decorative extra emoji (captions, headers, empty states) stays out. Ask Mike remains the yellow plate, alone on the last row.

## 6. Do's and Don'ts

### Do:
- **Do** keep the Mini App on Canvas (`#F4F7FB`) with Surface rows, Harbor Navy ink, and one Plate Yellow CTA.
- **Do** put Mike's circular portrait on the home hero and the wordmark PNG in the header.
- **Do** use 2-up topic tiles that match the bot keyboard, 96px min height, 44px+ hit targets, one emoji per circle.
- **Do** set live type in Golos Text; 16px body; sentence case; `text-wrap: pretty` on the greeting.
- **Do** keep ops UI task-dense: Harbor Navy buttons, 8px radius, no portrait, no plate yellow chrome.
- **Do** honor `prefers-reduced-motion`: instant color shifts, no transform.

### Don't:
- **Don't** build cringy consumer apps: over-cute copy, mascot spam, emoji walls, gamified fluff that undercuts trust.
- **Don't** use loud travel-agency Telegram spam or hard-sell real-estate brochure tone.
- **Don't** ship generic flashy SaaS dashboards that prioritize chrome over task completion (including the dark-navy advertiser mock from the sales PDF).
- **Don't** put beach photography, palms, or sunsets behind the UI. The Desk Rule.
- **Don't** use cream, sand, beige, or warm-paper body backgrounds.
- **Don't** use gradient text, glassmorphism, thick side-stripe borders, or identical icon+heading+text card grids.
- **Don't** use a tiny uppercase tracked eyebrow above every section.
- **Don't** treat the dark "night harbor" phone (navy screen, cyan «Спроси Майка!») as canonical. Light concierge won.
- **Don't** stack the full lockup (face + MIKE + PHUKET bar) inside the Mini App header. Face is the hero; wordmark is the header.
