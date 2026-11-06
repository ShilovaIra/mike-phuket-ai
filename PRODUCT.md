# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**Tourists (primary):** Russian-speaking visitors and newcomers on Phuket. They are on a phone, in Telegram chat or in the Mini App, often between places. They need a local answer quickly: where to eat, what to see, what's nearby, and optional help with property and partner services.

**Operators (secondary):** Phuket ProMax staff at a laptop. They run the bot from the admin: stats, broadcasts, places, the knowledge base, partners, and partner users. They want speed and clarity, not personality theater.

Job to be done for tourists: get a useful local answer fast, and when interested in real estate, leave a clean lead without a hard sell. Job for operators: schedule messages, keep places and partners current, and read what the bot is doing, with minimal friction.

## Product Purpose

Mike Phuket AI is a Telegram guide for Phuket and a soft assistant for Phuket ProMax. It answers practical travel questions, surfaces partner offers, and qualifies real-estate interest through short, sequential questions. Tourists meet Mike in chat and in the Telegram Mini App. Operators run that pipeline from the admin.

Success is a helpful chat that turns genuine interest into an actionable lead, and an admin that lets operators run the pipeline without ceremony.

## Positioning

A local guide inside Telegram that answers first and only then asks one or two questions. The Mini App carries the same guide: home, places, chat, saved, and profile. The bot keyboard stays the chat entry. The map tab is present and still marked soon.

## Operating Context

Tourists use a phone inside Telegram. The Mini App follows the phone's light or dark scheme unless the person has saved a choice (`mike-theme`).

Operators use a laptop. Broadcast times and partner-user timestamps are shown in Asia/Bangkok. The partner dashboard is a separate surface and is not this admin desk.

## Capabilities and Constraints

- Telegram bot: short Russian replies, a reply keyboard packed two-up with Ask Mike alone on the last row, partner offers, and sequential real-estate questions. Contact is shared when the person offers it.
- Mini App: home with Mike's photograph and an ask button, recommendations, places, chat, saved, and profile. The map tab is labeled soon. Home search and filters are in the markup and not live.
- Admin, signed in: stats, one-time and interval broadcasts, places and categories, knowledge base, partners, and partner users. Rail labels are Russian. The rail title reads "Admin Panel".
- Tourist copy is Russian.

## Brand Commitments

The name is Mike (Майк). Tourist voice: friendly, short, lively, clear Russian, one or two questions at a time. Operator voice: neutral, efficient, calm. The admin does not wear Mike's character.

Three words for Mike: friendly · clear · local. Three words for ops: neutral · efficient · calm.

Identity assets on hand: `mike-phuket-ai-tma/assets/hero-mike.jpg`, `mike-phuket-ai-tma/assets/mike-recommends.png`. Harbor Navy is the wordmark ink. There is no wordmark file in the repo.

Anti-references: cringy consumer apps (over-cute copy, mascot spam, emoji walls, gamified fluff), loud travel-agency Telegram spam and hard-sell real-estate brochure tone, and generic flashy SaaS dashboards that prioritize chrome over the task.

## Evidence on Hand

- Home photograph: `mike-phuket-ai-tma/assets/hero-mike.jpg`
- Recommendation mark: `mike-phuket-ai-tma/assets/mike-recommends.png`
- Empty place image: `mike-phuket-ai-tma/assets/empty_picture_placeholder.jpg`
- No testimonials, press quotes, pricing, or case studies are in the repo. Do not invent them.

## Product Principles

1. **Channel-fit first** — Telegram keyboards and messages stay scannable on a phone. The admin stays task-dense and quiet.
2. **Help before harvest** — Guide and answer first. Lead questions only when real-estate intent appears, and never all at once.
3. **Two voices, one product** — Mike stays warm for tourists. Operators get a neutral desk with no character cosplay.
4. **Specific over clever** — Labels name the action. No playful ambiguity.
5. **Trust by restraint** — No cringe, no hard sell, no decorative urgency. Confidence comes from a useful answer and a clean lead handoff.

## Accessibility & Inclusion

Aim for WCAG AA on the Mini App and the admin. Respect `prefers-reduced-motion`. Keep contrast readable. Don't rely on color alone for status. Telegram button labels stay short and unambiguous. The Mini App ships a light theme and a dark theme.
