# 🎨 CareerOS — UI/UX Design Brainstorm & Brand System (v2.0)

> **Versiyon:** v2.0.0 (Product Review Revizyonu)  
> **Tarih:** 14 Temmuz 2026  
> **Temel Felsefe:** "Observe → Understand → Act"  
> **Amaç:** Y Combinator demo-day seviyesinde, developer'ın düşünme biçimine uyan, sakin ve hikaye anlatan bir product

---

## 📋 İçindekiler

1. [Product Philosophy — 3 Katmanlı Mental Model](#1-product-philosophy)
2. [Brand DNA & Positioning](#2-brand-dna)
3. [Design Principles (Revize)](#3-design-principles)
4. [Visual Language System](#4-visual-language)
5. [Typography System](#5-typography)
6. [Color System](#6-color-system)
7. [Layout & Information Architecture](#7-layout)
8. [Dashboard — Hikaye Anlatan Homepage](#8-dashboard)
9. [9 Ekranın Revizyonu](#9-9-ekran)
10. [Evidence Studio (Yeni Konsept)](#10-evidence-studio)
11. [Career Timeline (Yeni Feature)](#11-career-timeline)
12. [Explainability Everywhere](#12-explainability)
13. [Micro-copy & Voice](#13-microcopy)
14. [Her Sayfa İçin 3 Soru](#14-3-soru)
15. [Implementation Plan](#15-implementation)

---

## 1. Product Philosophy — 3 Katmanlı Mental Model

### 1.1 Observe → Understand → Act

CareerOS'un mental modeli bu üç katmandan oluşur. Her feature, her ekran, her interaction bu üç katmandan birine hizmet eder.

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   OBSERVE          Sistem dünyayı izler                 │
│   ─────────        (Kullanıcı hiçbir şey yapmaz)        │
│                    Jobs, Companies, Market,             │
│                    GitHub, Applications, Memory         │
│                                                         │
│        ↓                                                │
│                                                         │
│   UNDERSTAND       Veri → Insight dönüşümü             │
│   ──────────       (Sistem kullanıcıya hikaye anlatır)  │
│                    "Bugün Almanya'da Rust %18 arttı.    │
│                     Sen %72'sine yakınsın.              │
│                     Tek eksik: Docker Compose."         │
│                                                         │
│        ↓                                                │
│                                                         │
│   ACT              Kullanıcı isterse hareket eder      │
│   ───              (CV, Mail, Interview, Roadmap)       │
│                    Her aksiyon bilinçli, explainable    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Neden Bu Model?

| Product | Neden Seviliyor | CareerOS Karşılığı |
|---|---|---|
| **Notion** | İnsan beyninin çalışma şeklini taklit ediyor | Observe-Understand-Act = Developer'ın kariyer düşünme biçimi |
| **Linear** | Developer'ın düşünme biçimine uyuyor | Keyboard-first, fast, no noise |
| **Claude** | Bilgi kusmuyor, "bugün senin için önemli olan bu" diyor | Hikaye anlatan dashboard |
| **Morning Brew (newsletter)** | Her sabah brief | Daily briefing homepage |

### 1.3 Product Distribution (Y Combinator Insight)

```
%20  Job Aggregation     → Kopyalanabilir (JobSpy, ApplyPilot)
%30  AI Intelligence     → Zamanla kopyalanabilir
%50  Product Experience  → Gerçek farklılaştırıcı
       ↓
       UX, explainability, daily briefing, sakin tasarım, karar desteği
```

**Bizim odak noktamız:** %50'lik kısım — "Bugün ne yapmam gerektiğini söylüyor" hissi.

---

## 2. Brand DNA & Positioning

### 2.1 Brand Archetype

**The Sage + The Creator** hybrid

### 2.2 Brand Positioning Statement

> **"CareerOS is the AI-native career operating system that observes your career landscape, understands what matters, and helps you act with intention."**

**Eski (v1.0):** "...treat their career like a product."  
**Yeni (v2.0):** "...observes, understands, acts."

### 2.3 Core Promise

> **"Your career, narrated."**

**Alternatif taglines:**
- "Every morning, a brief. Every decision, explained."
- "Observe. Understand. Act."
- "Your career deserves a story, not a spreadsheet."

### 2.4 Product Mantra

> **"Don't show data. Tell the story."**

Bu mantra her UX kararında referans noktası olacak.

---

## 3. Design Principles

### 3.1 7 Core Design Principles

```
┌─────────────────────────────────────────────────────────────┐
│                  CAREEROS DESIGN MANIFESTO v2.0              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. NARRATE, DON'T DISPLAY                                   │
│     → Dashboard grafik çöplüğü değil, hikaye anlatır.        │
│                                                              │
│  2. EXPLAIN EVERYTHING                                       │
│     → Her score, her insight, her öneri "Why?" butonu taşır. │
│                                                              │
│  3. CALM OVER NOISY                                          │
│     → 50 grafik değil, 3 önemli şey.                         │
│                                                              │
│  4. AI SUGGESTS, HUMAN DECIDES                               │
│     → Otomatik başvuru yok. Her aksiyon bilinçli.            │
│                                                              │
│  5. EVIDENCE OVER CLAIM                                      │
│     → CV editörü yok. Evidence Studio var.                   │
│                                                              │
│  6. RESPECT USER'S TIME                                      │
│     → Keyboard-first. Cmd+K. 2 saniyede cevap.               │
│                                                              │
│  7. DARK MODE IS DEFAULT                                     │
│     → Developer'lar karanlıkta yaşar.                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Anti-Patterns

| Yapma | Yerine |
|---|---|
| ❌ Dashboard = 50 grafik | ✅ Dashboard = 3 önemli hikaye |
| ❌ CV Editor | ✅ Evidence Studio (kanıt tabanlı) |
| ❌ Job List | ✅ Opportunity Feed (scored, explained) |
| ❌ Learning = Udemy listesi | ✅ Learning = ROI-based projection |
| ❌ Analytics = grafik çöplüğü | ✅ Analytics = narrative funnel |
| ❌ Company = CRM | ✅ Company = Living Organism |
| ❌ Auto-apply | ✅ Conscious apply with explanation |

---

## 4. Visual Language System

### 4.1 Logo & Identity

**Primary:** "CareerOS" wordmark  
**Icon:** Circuit-pattern monogram "C"  
**Signature:** Indigo → Violet gradient (sparingly used)

### 4.2 Shape Language

- Small radius (4px): Code, tags
- Medium (6-8px): Buttons, inputs, cards
- Large (12px): Modals
- Full: Avatars, pills

### 4.3 Depth System

```
Level 0: Background (bg-background)
Level 1: Surface (cards, sidebar)
Level 2: Elevated (dropdowns)
Level 3: Modal (dialogs + backdrop-blur)
Level 4: Toast (notifications)
```

### 4.4 Icon System

**Library:** Lucide React (stroke 1.5px)

**Custom Icons:**
- `ObserveIcon` — Eye + signal waves
- `UnderstandIcon` — Brain + lightbulb
- `ActIcon` — Hand + arrow
- `EvidenceIcon` — Document + checkmark + graph
- `TimelineIcon` — Vertical line with dots
- `CareerIcon` — Briefcase + path

---

## 5. Typography System

### 5.1 Font Stack

- **Primary:** Inter (variable, 400-700)
- **Monospace:** JetBrains Mono (variable)
- **Display:** Geist (optional, hero only)

### 5.2 Type Scale

```css
--text-xs:   0.75rem;   /* 12px — captions */
--text-sm:   0.875rem;  /* 14px — secondary */
--text-base: 1rem;      /* 16px — body */
--text-lg:   1.125rem;  /* 18px — lead */
--text-xl:   1.25rem;   /* 20px — section */
--text-2xl:  1.5rem;    /* 24px — page */
--text-3xl:  1.875rem;  /* 30px — hero */
```

### 5.3 Narrative Typography

Hikaye anlatan sayfalarda typography hiyerarşisi:

```
Good evening, Abdullokh.              ← 2xl, semibold, personal
─────────────────────────────────────
You have 17 new opportunities.        ← base, normal, calm
4 of them are unusually strong.       ← base, medium, highlighted
One company started sponsoring visas. ← base, normal
Your interview is in 3 days.          ← base, warning color
Rust demand increased by 11%.         ← base, accent color
```

**Kural:** Her cümle tek satır. Kısa. Sakin. Hikaye anlatır.

---

## 6. Color System

### 6.1 Base Palette

Zinc scale (dark mode default) + Indigo/Violet accent.

### 6.2 Narrative Colors

Hikaye anlatımında renk semantik kullanımı:

| Context | Color | Usage |
|---|---|---|
| **Neutral information** | Zinc-400 | "You have 17 new opportunities" |
| **Highlighted insight** | Accent (indigo) | "4 are unusually strong" |
| **Positive change** | Emerald-500 | "Rust demand +11%" |
| **Negative change** | Rose-500 | "PHP demand -8%" |
| **Warning / Deadline** | Amber-500 | "Interview in 3 days" |
| **Opportunity** | Indigo-500 | "Company started sponsoring visas" |
| **Action needed** | Accent gradient | Primary CTA |

**Kural:** Dashboard'da maksimum 3 renk. Fazla renk = gürültü.

---

## 7. Layout & Information Architecture

### 7.1 Mental Model Mapping to Navigation

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR NAVIGATION                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊  Briefing         ← OBSERVE + UNDERSTAND (homepage) │
│                                                          │
│  📬  Inbox            ← OBSERVE (opportunity feed)      │
│  🏢  Companies        ← OBSERVE (living profiles)       │
│  📈  Market           ← OBSERVE (signals, trends)       │
│                                                          │
│  🎯  Evidence Studio  ← UNDERSTAND (new!)               │
│  📄  Resume Studio    ← ACT (evidence → CV)             │
│  📋  Applications     ← ACT (pipeline)                  │
│  🎓  Learning         ← ACT (roadmap)                   │
│                                                          │
│  📉  Analytics        ← UNDERSTAND (narrative)          │
│  ⏳  Timeline         ← OBSERVE (career memory, new!)   │
│  ⚙️  Settings         ← (configuration)                 │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Toplam:** 11 ekran (9 + Evidence Studio + Timeline)

### 7.2 Layout Grid

```
┌──────────────────────────────────────────────────┐
│  Topbar (h-14)                                    │
├──────────┬───────────────────────────────────────┤
│ Sidebar  │  Main Content                         │
│ (w-64)   │  (max-w-4xl, mx-auto, py-12)          │
│          │                                        │
│          │  ┌────────────────────────────────┐   │
│          │  │  Narrative Container           │   │
│          │  │  (single column, prose-style)  │   │
│          │  └────────────────────────────────┘   │
│          │                                        │
└──────────┴───────────────────────────────────────┘
```

**Not:** Dashboard `max-w-4xl` (narrower, prose-style). 50-column grid değil, narrative column.

---

## 8. Dashboard — Hikaye Anlatan Homepage

### 8.1 Design Philosophy

**Eski (v1.0):** 4 stat kartı + 2 chart + 2 liste  
**Yeni (v2.0):** Narrative briefing + Today's Focus + Opportunity Feed + Market Pulse

### 8.2 Dashboard Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Good evening, Abdullokh.                                    │
│  Tuesday, July 14, 2026                                      │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  You have 17 new opportunities.                              │
│  4 of them are unusually strong.                             │
│  One company started sponsoring visas.                       │
│  Your interview at Google is in 3 days.                      │
│  Rust demand increased by 11% this week.                     │
│                                                              │
│  [Read full briefing →]                                       │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  TODAY'S FOCUS                                               │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ○  Apply to Stripe — Backend Engineer                 │ │
│  │     Score: 87 · Deadline: 5 days · [Why strong →]      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  ○  Update Backend resume for Spotify opportunity       │ │
│  │     Evidence gap: Rust projects · [View gap →]         │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  ○  Review MongoDB before Google interview              │ │
│  │     Interview: Friday 2pm · [Study plan →]             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  OPPORTUNITY FEED                                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  87  Stripe · Backend Engineer · Remote · APPLY        │ │
│  │  ──────────────────────────────────────────────────── │ │
│  │  Why: Strong Rust match (+28), Unicorn tier (+12),     │ │
│  │       remote fits your preference (+8)                 │ │
│  │  Gap: Kafka experience                                 │ │
│  │                                                        │ │
│  │  [View details]  [Generate resume]  [Apply]            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  82  Anthropic · Research Engineer · SF · APPLY        │ │
│  │  ...                                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [+ 15 more in Inbox →]                                      │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  MARKET PULSE                                                │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ Rust     │ │ K8s      │ │ Python   │ │ PHP      │        │
│  │ +11% 📈  │ │ +7% 📈   │ │ stable   │ │ -8% 📉   │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│                                                              │
│  [Full market report →]                                      │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  APPLICATION PIPELINE                                        │
│                                                              │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐             │
│  │TO APPLY│→ │APPLIED │→ │INTERV. │→ │ OFFER  │             │
│  │  (5)   │  │  (12)  │  │  (3)   │  │  (1)   │             │
│  └────────┘  └────────┘  └────────┘  └────────┘             │
│                                                              │
│  This month: 29 applied → 13 responses (45%)                 │
│  [View pipeline →]                                           │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  LEARNING FOCUS                                              │
│                                                              │
│  If you learn Kafka this month:                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  +231 new jobs unlocked                                 │ │
│  │  +18% average salary                                    │ │
│  │  14 hours to learn                                      │ │
│  │  ROI: 9.7 / 10                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [View full roadmap →]                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Dashboard Sections

| Section | Purpose | Length |
|---|---|---|
| **Greeting + Brief** | Hikaye anlatır, 5 satır max | 6 lines |
| **Today's Focus** | 3 tane aksiyon, bitti | 3 items |
| **Opportunity Feed** | Top 2-3 jobs with explanation | 2-3 cards |
| **Market Pulse** | 4 skill trend, simple | 4 badges |
| **Application Pipeline** | Funnel visualization | 1 row |
| **Learning Focus** | 1 ROI projection | 1 card |

**Kural:** Her section "→" ile detay sayfasına yönlendirir. Dashboard özet, detay sayfada.

---

## 9. 11 Ekranın Tasarımı

### 9.1 Briefing (Homepage) — `/`

**Eski:** 4 stat kartı + chart grid  
**Yeni:** Narrative storytelling (Section 8'deki gibi)

**3 Soru:**
- **Hangi soruyla geliyor?** "Bugün ne yapmalıyım?"
- **Hangi kararı vermiş olacak?** 3 aksiyondan birini seçecek
- **Sonraki doğal adım?** Today's Focus'taki aksiyonu yapmak

---

### 9.2 Inbox — `/inbox`

**Eski:** Job list + detail panel  
**Yeni:** Opportunity Feed with explanation (her job "Why?" ile)

```
┌─────────────────────────────────────────────────────────────┐
│  Inbox · 156 opportunities                                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  87  APPLY    Stripe · Backend Engineer                 │ │
│  │  ──────────────────────────────────────────────────── │ │
│  │                                                        │ │
│  │  Why this score?                                       │ │
│  │                                                        │ │
│  │  ✔ Rust experience (you: 82%, they need: high)         │ │
│  │  ✔ Kubernetes (matched)                                │ │
│  │  ✔ OSS activity (they value it)                        │ │
│  │  ✔ Similar company history (Unicorn → Unicorn)         │ │
│  │                                                        │ │
│  │  ⚠ Missing: Kafka                                      │ │
│  │  ⚠ German B2 required (for Berlin office)              │ │
│  │                                                        │ │
│  │  Fit: 85   Acceptance: 72   Career: 91   Market: 80   │ │
│  │                                                        │ │
│  │  [View company]  [Generate resume]  [Apply]            │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Bu iş bana uygun mu?"
- **Hangi kararı vermiş olacak?** Apply / Skip / Learn gap
- **Sonraki doğal adım?** Generate resume veya Apply

---

### 9.3 Companies — `/companies`

**Eski:** Company list + detail panel  
**Yeni:** Living Organism (şirket yaşayan bir organizma gibi)

```
┌─────────────────────────────────────────────────────────────┐
│  Stripe                                                       │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  ┌──────┐                                                    │
│  │  S   │  Unicorn · Fintech · San Francisco                │
│  └──────┘  8,000 employees · Founded 2010                    │
│                                                              │
│  HIRING TREND                                                 │
│  📈 SPIKE · 12 new positions this week (+4 vs last week)     │
│                                                              │
│  TECH STACK                                                   │
│  [Ruby] [Go] [Rust] [Python] [Kafka] [AWS] [Scala]           │
│                                                              │
│  VISA                                                         │
│  ✓ H1B sponsorship (for US)                                  │
│  ✓ EU Blue Card (for Europe)                                 │
│                                                              │
│  YOUR HISTORY                                                 │
│  • 2026-05-12: Applied to Backend Engineer (rejected, phone) │
│  • Topics asked: Docker, Redis, system design                │
│  • Advice: Wait 6+ months or strengthen distributed systems  │
│                                                              │
│  [View full memory →]  [Add note]                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Bu şirket nasıl bir yer, başvurmalı mıyım?"
- **Hangi kararı vermiş olacak?** Apply / Research more / Skip
- **Sonraki doğal adım?** Inbox'ta bu şirketin ilanlarına bak

---

### 9.4 Evidence Studio (YENİ) — `/evidence`

**Eski:** Resume Studio (CV editörü)  
**Yeni:** Evidence Studio (kanıt tabanlı skill exploration)

```
┌─────────────────────────────────────────────────────────────┐
│  Evidence Studio                                               │
│  Your skills, proven by evidence                              │
│                                                              │
│  SKILLS BY CONFIDENCE                                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Python                                     92% ████   │ │
│  │  6 projects · 1,847 commits · 89 stars                │ │
│  │  [View evidence →]                                     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  Computer Vision                            85% ████   │ │
│  │  3 projects · 412 commits · 38 stars                  │ │
│  │  [View evidence →]                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  EVIDENCE DETAIL: Python                                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  📁 Project-Drone-Vision                               │ │
│  │  142 commits · 38 stars · 13M LOC                      │ │
│  │  topics: yolov8, opencv, computer-vision               │ │
│  │  has_tests: ✓  ·  has_docs: ✓  ·  has_releases: ✗     │ │
│  │                                                        │ │
│  │  Evidence for: [Python] [CV] [PyTorch] [OpenCV]        │ │
│  │  [View on GitHub]  [Use in resume →]                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  EVIDENCE GAPS                                                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ⚠ Kubernetes                                          │ │
│  │     Required by: 142 jobs you match otherwise          │ │
│  │     Learning time: 20 hours                            │ │
│  │     [Start learning →]                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Hangi skill'lerim kanıtlanmış, hangileri eksik?"
- **Hangi kararı vermiş olacak?** Eksik skill'i öğren veya kanıtlanmış skill'i CV'de kullan
- **Sonraki doğal adım?** Learning roadmap veya Resume Studio

---

### 9.5 Resume Studio — `/resume`

**Eski:** CV editor with form  
**Yeni:** Evidence → Resume generator (3-step wizard)

```
┌─────────────────────────────────────────────────────────────┐
│  Resume Studio                                                │
│                                                              │
│  STEP 1: CHOOSE TARGET                                        │
│  Company:  [Google ▼]   Role: [ML Engineer ▼]                │
│  Template: [ML Research ▼]                                    │
│                                                              │
│  STEP 2: SELECT EVIDENCE                                      │
│  AI suggests these based on target:                          │
│  ✓ Project-Drone-Vision (CV, YOLOv8)              [remove]   │
│  ✓ IMMUNO-TCR (research, PyTorch)                 [remove]   │
│  ☐ sentiment-analyzer (NLP)                       [add]      │
│                                                              │
│  STEP 3: GENERATE                                             │
│  [Generate Resume ✨]                                         │
│                                                              │
│  PREVIEW                                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  # Abdullokh Abdukodirov · ML Engineer | Google        │ │
│  │  ...                                                   │ │
│  │  [Download PDF]  [Copy Markdown]  [Edit evidence]      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Bu iş için hangi CV'yi oluşturmalıyım?"
- **Hangi kararı vermiş olacak?** Evidence seçip CV generate edecek
- **Sonraki doğal adım?** Applications'a ekle veya direkt Apply

---

### 9.6 Applications — `/applications`

**Eski:** Kanban board  
**Yeni:** Kanban + Timeline tab

```
┌─────────────────────────────────────────────────────────────┐
│  Applications · 29 total                                      │
│  [Pipeline]  [Timeline]  [Analytics]                          │
│                                                              │
│  PIPELINE VIEW                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │ TO APPLY │→│ APPLIED  │→│ INTERV.  │→│ OFFER    │         │
│  │   (5)    │ │  (12)    │ │   (3)    │ │   (1)    │         │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘         │
│                                                              │
│  THIS MONTH                                                   │
│  29 applied → 13 responses (45%)                             │
│  3 interviews · 1 offer                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Başvurularım ne durumda?"
- **Hangi kararı vermiş olacak?** Follow-up yap veya yeni başvuru ekle
- **Sonraki doğal adım?** Inbox'a dön

---

### 9.7 Market — `/market`

**Eski:** Signal list + trend charts  
**Yeni:** Narrative market report

```
┌─────────────────────────────────────────────────────────────┐
│  Market Intelligence                                          │
│                                                              │
│  THIS WEEK'S STORY                                            │
│                                                              │
│  The backend engineer market shifted noticeably this week.   │
│  Rust demand climbed 11%, while PHP dropped 8%.              │
│                                                              │
│  Three companies worth watching:                             │
│  • Stripe started hiring aggressively (12 new roles)         │
│  • Anthropic raised $4B Series D (expansion signal)          │
│  • Intel laid off 5,000 (avoid for now)                      │
│                                                              │
│  For your profile, this means:                               │
│  Your Rust skills are becoming more valuable.                │
│                                                              │
│  SKILL TRENDS                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ Rust +11%│ │ K8s +7%  │ │Python st.│                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
│                                                              │
│  SIGNALS                                                      │
│  🔥 Anthropic raises $4B · Impact: More ML roles coming      │
│  ⚠ Intel lays off 5,000 · Impact: Avoid for 6 months        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Piyasada ne oluyor, benim için ne anlama geliyor?"
- **Hangi kararı vermiş olacak?** Bir skill'i öğren veya bir şirkete başvur
- **Sonraki doğal adım?** Learning veya Inbox

---

### 9.8 Learning — `/learning`

**Eski:** Skill list + roadmap  
**Yeni:** ROI-based projection

```
┌─────────────────────────────────────────────────────────────┐
│  Learning                                                     │
│  Skills worth learning, proven by ROI                         │
│                                                              │
│  YOUR NEXT BEST MOVE                                          │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  If you learn Kafka this month:                        │ │
│  │                                                        │ │
│  │  +231 new jobs unlocked                                │ │
│  │  +18% average salary (vs your current)                 │ │
│  │  14 hours to learn                                     │ │
│  │  ROI: 9.7 / 10                                         │ │
│  │                                                        │ │
│  │  Why Kafka?                                            │ │
│  │  • Required by 231 jobs you otherwise match            │ │
│  │  • Trending up (+7% this week)                         │ │
│  │  • Your Python/Go skills transfer well                 │ │
│  │                                                        │ │
│  │  [Start learning →]  [View learning path →]            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  YOUR ROADMAP — 12 weeks                                      │
│  Week 1-2:  Kafka (14h → 231 jobs, ROI 9.7)         ████░░░  │
│  Week 3-4:  Docker (12h → 91 jobs, ROI 7.5)         ░░░░░░░  │
│  Week 5-6:  Kubernetes (20h → 142 jobs, ROI 7.1)    ░░░░░░░  │
│                                                              │
│  COMPLETED SKILLS                                             │
│  ✓ Rust — 45h — Unlocked: 67 new jobs, +40% interview rate  │
│  ✓ System Design — 30h — Unlocked: 89 new jobs              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Hangi skill'i öğrenmeliyim?"
- **Hangi kararı vermiş olacak?** En yüksek ROI'li skill'i seçecek
- **Sonraki doğal adım?** Learning path'i başlat

---

### 9.9 Analytics — `/analytics`

**Eski:** Chart grid  
**Yeni:** Narrative funnel

```
┌─────────────────────────────────────────────────────────────┐
│  Analytics · Last 30 days                                     │
│                                                              │
│  THIS MONTH'S STORY                                           │
│  You applied to 32 jobs.                                       │
│  5 of them responded (16% response rate).                      │
│  3 made it to interview stage.                                 │
│  1 resulted in an offer.                                       │
│                                                              │
│  WHAT CHANGED?                                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Resume v7 (introduced June 28)                        │ │
│  │  Before v7: 8% response rate                           │ │
│  │  After v7:  16% response rate (+100%)                  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  BY COMPANY TIER                                              │
│  Big Tech    45% of apps  ·  12% response                    │
│  Unicorn     30% of apps  ·  22% response  ← best            │
│  Large       15% of apps  ·  18% response                    │
│                                                              │
│  Insight: Unicorns respond 2x more than Big Tech.            │
│  Consider shifting 30% of Big Tech apps to Unicorns.         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Performansım nasıl, neyi geliştirmeliyim?"
- **Hangi kararı vermiş olacak?** Strateji değiştirecek
- **Sonraki doğal adım?** Inbox'a dön, yeni stratejiyi uygula

---

### 9.10 Settings — `/settings`

```
┌─────────────────────────────────────────────────────────────┐
│  Settings                                                     │
│  PROFILE · WEIGHTS · PREFERENCES · PRIVACY · INTEGRATIONS    │
│                                                              │
│  SCORING WEIGHTS                                              │
│  How CareerOS ranks opportunities for you:                   │
│                                                              │
│  Fit Score           ████████░░  30%                          │
│  Acceptance Prob     ███████░░░  25%                          │
│  Career Value        ███████░░░  25%                          │
│  Market Demand       ██████░░░░  20%                          │
│                                                              │
│  Why these weights?                                          │
│  You've historically accepted roles with high career value   │
│  over high salary. CareerOS learned this from your actions.  │
│                                                              │
│  [Adjust weights]  [Reset to default]                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### 9.11 Career Timeline (YENİ) — `/timeline`

**Phase 5 feature, UI placeholder Phase 4'te**

```
┌─────────────────────────────────────────────────────────────┐
│  Career Timeline                                              │
│  Your career memory, visualized                               │
│                                                              │
│  2026                                                         │
│  ────                                                         │
│                                                              │
│  ● Jul 14 — Offer received from Stripe ($280k)               │
│    └─ First offer in CareerOS                                │
│                                                              │
│  ● Jul 10 — Interview at Stripe (onsite)                     │
│    └─ Topics: System design, API design                      │
│                                                              │
│  ● Jun 28 — Resume v7 created                                │
│    └─ Response rate doubled (8% → 16%)                       │
│                                                              │
│  ● Jun 15 — Learned Rust                                     │
│    └─ 45 hours · Unlocked 67 new jobs                        │
│                                                              │
│  ● May 12 — Applied to Stripe (first attempt)                │
│    └─ Rejected at phone screen                               │
│                                                              │
│  2025                                                         │
│  ────                                                         │
│                                                              │
│  ● Nov 03 — Started at Current Company                       │
│    └─ Backend Engineer · $145k                               │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  KEY MILESTONES                                               │
│  🎓 1 graduation   💼 2 job changes   🎯 4 skills learned    │
│  📄 7 resume versions   📨 127 applications   💰 +$135k      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**3 Soru:**
- **Hangi soruyla geliyor?** "Kariyerimde nereden nereye geldim?"
- **Hangi kararı vermiş olacak?** Progress'i görecek, motive olacak
- **Sonraki doğal adım?** Briefing'e dön

---

## 10. Evidence Studio — Konsept

### 10.1 Neden CV Editörü Değil?

| CV Editor (Geleneksel) | Evidence Studio (CareerOS) |
|---|---|
| Kullanıcı boş form doldurur | Sistem kanıtları gösterir |
| "Passionate developer" yazar | "142 commits, 38 stars" gösterir |
| Generic CV üretir | Target-aware CV üretir |
| Claim-based | Evidence-based |

### 10.2 Evidence Studio User Flow

```
1. User opens Evidence Studio
   ↓
2. Sees skills ranked by confidence
   ↓
3. Clicks a skill (e.g., "Python")
   ↓
4. Sees all evidence: projects, commits, stars, LOC, quality signals
   ↓
5. Clicks "Use in resume"
   ↓
6. System suggests target companies where this skill is valued
   ↓
7. User selects target → Resume Studio generates evidence-based CV
```

### 10.3 Components

**SkillConfidenceCard:**

```
┌────────────────────────────────┐
│ Python                  92%    │
│ ━━━━━━━━━━━━━━━━━━━━━━━        │
│ 6 projects · 1,847 commits     │
│ 89 stars · 45 topics           │
│ [View evidence →]              │
└────────────────────────────────┘
```

**EvidenceDetailCard:**

```
┌────────────────────────────────────────┐
│ 📁 Project-Drone-Vision                │
│ 142 commits · 38 stars · 13M LOC       │
│ topics: yolov8, opencv, cv             │
│ ✓ has_tests  ✓ has_docs  ✗ has_releases│
│ Evidence for: [Python] [CV] [PyTorch]  │
│ [View on GitHub]  [Use in resume →]    │
└────────────────────────────────────────┘
```

---

## 11. Career Timeline — Konsept

### 11.1 Vision

> **"Your career, narrated over years."**

Kullanıcı yıllarca kullandıkça sistem onun career memory'si olur.

### 11.2 Data Sources

```
Timeline Events
├─ Applications (Phase 1'de var)
├─ Skills learned (Phase 2'de var)
├─ Resume versions (Phase 2'de var)
├─ Interview outcomes (Phase 1'de var)
├─ Offers received (Phase 1'de var)
├─ Job changes (Phase 1'de var)
├─ Market milestones (Phase 3'de var)
└─ Personal milestones (manual entry)
```

### 11.3 Backend Sketch (Phase 5)

```python
# services/learning_engine/career_timeline.py
class CareerTimelineService:
    def get_timeline(self, user_id: str, years: int = 5) -> List[TimelineEvent]:
        events = []
        events.extend(self._get_application_events(user_id))
        events.extend(self._get_skill_events(user_id))
        events.extend(self._get_resume_events(user_id))
        events.extend(self._get_offer_events(user_id))
        events.extend(self._get_milestone_events(user_id))
        return sorted(events, key=lambda e: e.timestamp, reverse=True)
```

---

## 12. Explainability Everywhere

### 12.1 "Why?" Pattern

Her sayı, her insight, her öneri "Why?" butonu taşır.

```
┌──────────┐        ┌────────────────────────────────────────┐
│  87      │ click  │ Why 87?                                │
│  APPLY   │ ──────►│ ✔ Rust experience (+28)                │
│ [Why? →] │        │ ✔ Kubernetes (+15)                     │
└──────────┘        │ ✔ OSS activity (+12)                   │
                    │ ⚠ Missing Kafka (-8)                   │
                    │ Base: 50 + adjustments = 87            │
                    └────────────────────────────────────────┘
```

### 12.2 Explainability Checklist

| Element | Has "Why?" |
|---|---|
| Career Score | ✓ |
| Recommendation (APPLY/CONSIDER/SKIP) | ✓ |
| Skill Confidence | ✓ |
| Market Trend | ✓ |
| Learning ROI | ✓ |
| Company Tier | ✓ |
| Interview Difficulty | ✓ |
| Resume Suggestion | ✓ |
| Weight Adjustment | ✓ |

---

## 13. Micro-copy & Voice

### 13.1 Voice Principles

| Principle | DO | DON'T |
|---|---|---|
| **Narrative** | "You have 17 new opportunities" | "Opportunities: 17" |
| **Calm** | "4 of them are unusually strong" | "🔥🔥 4 HOT OPPORTUNITIES!!!" |
| **Specific** | "Rust demand +11% this week" | "Rust is trending" |
| **Honest** | "Low acceptance probability (32%)" | "This might be challenging" |
| **Actionable** | "Study Docker to unlock 91 jobs" | "Consider learning Docker" |

### 13.2 Narrative Templates

```
Greeting:    "Good {time_of_day}, {name}."
Brief:       "You have {N} new opportunities."
             "{M} of them are unusually strong."
             "Your interview at {company} is in {N} days."
             "{skill} demand increased by {N}% this week."
Focus item:  "○ {action} — {context}"
Insight:     "{applications} applied → {responses} responses ({rate}%)"
```

### 13.3 Date Formatting

```typescript
formatBriefDate(date)    // "today", "tomorrow", "in 3 days"
formatTimelineDate(date) // "Jul 14, 2026" (absolute)
formatRelative(date)     // "2h ago", "Yesterday", "3d ago"
```

---

## 14. Her Sayfa İçin 3 Soru

### 14.1 The 3-Question Rule

Her sayfa için bu 3 sorunun net cevabı olmalı:

| Soru | Neden Önemli |
|---|---|
| **Kullanıcı hangi soruyla geliyor?** | Sayfanın amacı netleşir |
| **Hangi kararı vermiş olacak?** | Her sayfa bir decision point |
| **Sonraki doğal adım ne?** | Navigation flow mantıklı olur |

### 14.2 Tüm Sayfalar

| Sayfa | Hangi Soruyla? | Hangi Karar? | Sonraki Adım |
|---|---|---|---|
| **Briefing** | "Bugün ne yapmalıyım?" | 3 aksiyondan birini seç | Today's Focus'taki aksiyonu yap |
| **Inbox** | "Bu iş bana uygun mu?" | Apply / Skip / Learn gap | Generate resume veya Apply |
| **Companies** | "Bu şirket nasıl?" | Apply / Research / Skip | Inbox'ta bu şirketin ilanları |
| **Evidence Studio** | "Hangi skill'lerim kanıtlanmış?" | Öğren / CV'de kullan | Learning veya Resume Studio |
| **Resume Studio** | "Bu iş için hangi CV?" | Evidence seç, CV generate | Applications'a ekle veya Apply |
| **Applications** | "Başvurularım ne durumda?" | Follow-up / Yeni başvuru | Inbox'a dön |
| **Market** | "Piyasada ne oluyor?" | Skill öğren / Şirkete başvur | Learning veya Inbox |
| **Learning** | "Hangi skill'i öğrenmeliyim?" | En yüksek ROI'li skill | Learning path başlat |
| **Analytics** | "Performansım nasıl?" | Strateji değiştir | Inbox'a dön |
| **Timeline** | "Nereden nereye geldim?" | Progress gör | Briefing'e dön |
| **Settings** | "Nasıl özelleştirebilirim?" | Weights/preferences | Briefing'e dön |

### 14.3 Navigation Flow

```
                    ┌──────────────┐
                    │   Briefing   │ ← Her gün buradan başla
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌──────────┐     ┌────────────┐    ┌──────────┐
   │  Inbox   │     │  Evidence  │    │  Market  │
   └────┬─────┘     │   Studio   │    └────┬─────┘
        │           └─────┬──────┘         │
        └────────────────►│◄───────────────┘
                          ▼
                   ┌────────────┐
                   │   Resume   │
                   │   Studio   │
                   └─────┬──────┘
                         ▼
                   ┌────────────┐
                   │Applications│
                   └─────┬──────┘
              ┌──────────┴──────────┐
              ▼                     ▼
       ┌────────────┐        ┌──────────┐
       │ Analytics  │        │ Timeline │
       └────────────┘        └──────────┘
              └──────────┬──────────┘
                         ▼
                   ┌────────────┐
                   │  Briefing  │ (döngü)
                   └────────────┘
```

---

## 15. Implementation Plan

### 15.1 Week-by-Week Breakdown

#### **Week 1: Foundation + Narrative Dashboard** (10 saat)

| Day | Task | Output |
|---|---|---|
| 1 | Next.js + shadcn/ui + design tokens | Running dev server |
| 2 | Layout + Sidebar + Cmd+K | Navigation system |
| 3 | Narrative Dashboard (Briefing) | Homepage with storytelling |
| 4 | Today's Focus component | 3-action card |
| 5 | Opportunity Feed component | Job card with "Why?" |
| 6 | Market Pulse component | 4 skill trends |
| 7 | API client + TypeScript types | Type-safe fetching |

#### **Week 2: Core Pages** (10 saat)

| Day | Task | Output |
|---|---|---|
| 1 | Inbox screen (Opportunity Feed) | With explanation modals |
| 2 | Companies screen (Living Organism) | Company detail page |
| 3 | Evidence Studio (skill list + detail) | Core konsept |
| 4 | Resume Studio (3-step wizard) | Evidence → CV |
| 5 | Applications (Kanban + Timeline placeholder) | Pipeline view |

#### **Week 3: Secondary Pages + Polish** (10 saat)

| Day | Task | Output |
|---|---|---|
| 1 | Market screen (narrative report) | Story-telling market |
| 2 | Learning screen (ROI projections) | Not Udemy list |
| 3 | Analytics screen (narrative funnel) | Story-telling analytics |
| 4 | Timeline screen (placeholder) | Coming soon |
| 5 | Settings + polish + dark mode | Complete system |

### 15.2 Technical Stack

```
Frontend:
├── Next.js 14 (App Router)
├── React 18
├── TypeScript
├── Tailwind CSS
├── shadcn/ui (Radix primitives)
├── Recharts (data viz, sparingly)
├── TanStack Query (data fetching)
├── Zustand (client state)
├── Framer Motion (subtle animations)
├── Lucide React (icons)
├── date-fns (date formatting)
└── Sonner (toasts)
```

### 15.3 File Structure

```
apps/web/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                # Briefing (narrative homepage)
│   ├── inbox/page.tsx
│   ├── companies/
│   │   ├── page.tsx
│   │   └── [name]/page.tsx
│   ├── evidence/page.tsx       # Evidence Studio
│   ├── resume/page.tsx
│   ├── applications/page.tsx
│   ├── market/page.tsx
│   ├── learning/page.tsx
│   ├── analytics/page.tsx
│   ├── timeline/page.tsx       # Placeholder (Phase 5)
│   └── settings/page.tsx
│
├── components/
│   ├── ui/                     # shadcn/ui
│   ├── narrative/              # Narrative components
│   │   ├── brief-sentence.tsx
│   │   ├── todays-focus.tsx
│   │   ├── opportunity-card.tsx
│   │   ├── insight-card.tsx
│   │   └── why-button.tsx
│   ├── evidence/               # Evidence Studio
│   │   ├── skill-confidence-card.tsx
│   │   ├── evidence-detail-card.tsx
│   │   └── evidence-gap-card.tsx
│   ├── timeline/               # Timeline
│   │   ├── timeline-event.tsx
│   │   └── milestone-card.tsx
│   └── layout/
│       ├── sidebar.tsx
│       ├── topbar.tsx
│       └── command-palette.tsx
│
├── lib/
│   ├── api.ts
│   ├── types.ts
│   ├── narrative.ts            # Narrative formatting utils
│   └── utils.ts
│
└── hooks/
    ├── use-jobs.ts
    ├── use-companies.ts
    └── use-theme.ts
```

### 15.4 Narrative Components API

**BriefSentence:**

```tsx
interface BriefSentenceProps {
  children: React.ReactNode;
  highlight?: boolean;
  tone?: "neutral" | "positive" | "negative" | "warning" | "opportunity";
}

<BriefSentence>You have 17 new opportunities.</BriefSentence>
<BriefSentence highlight>4 of them are unusually strong.</BriefSentence>
<BriefSentence tone="warning">Interview at Google is in 3 days.</BriefSentence>
```

**TodaysFocus:**

```tsx
interface TodaysFocusItem {
  action: string;
  context: string;
  href: string;
  whyLabel: string;
}

<TodaysFocus items={[
  {
    action: "Apply to Stripe",
    context: "Backend Engineer · Score: 87 · Deadline: 5 days",
    href: "/inbox/stripe-backend",
    whyLabel: "Why strong?"
  }
]} />
```

**WhyButton:**

```tsx
interface WhyButtonProps {
  score: number;
  breakdown: { label: string; value: number; positive: boolean }[];
}

<ScoreBadge score={87}>
  <WhyButton score={87} breakdown={breakdown} />
</ScoreBadge>
```

---

## Başlangıç Komutları

```bash
# 1. Next.js setup
cd apps/web
npx create-next-app@latest . --typescript --tailwind --app --eslint

# 2. shadcn/ui
npx shadcn@latest init

# 3. Core deps
npm install @tanstack/react-query zustand framer-motion lucide-react date-fns sonner

# 4. Design tokens → globals.css

# 5. Layout → sidebar + topbar + Cmd+K

# 6. Narrative Homepage (Briefing)
```

---

*Bu doküman Phase 4 Frontend'in tasarım spesifikasyonudur. Backend (Phase 1-3) %100 tamamlandı, LOCKED. Sonraki adım: `apps/web/` kurulumu.*
