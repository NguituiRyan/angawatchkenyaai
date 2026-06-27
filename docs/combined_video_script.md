# Presentation video — pitch deck + live demo (≤3 min)

Brief: first ~1–1.5 min = walk the pitch deck (face-cam + slides); final ~1.5–2 min = the
prototype, showing BOTH user flows (farmer + cooperative). ~430 words ≈ 3:00.

## Before you record
- [ ] Reboot the deployed app (current build, Neo4j live).
- [ ] WhatsApp: re-open the Twilio sandbox window (<24 h) from the farmer phone; don't burn
      the 50/day cap; keep the phone visible. Fallback: the dashboard alert card + a prior
      WhatsApp screenshot.
- [ ] Record **yourself + your screen** (Loom). Face-cam over the slides for Part 1; screen
      for Part 2. You may pause/continue between flows.

---

## PART 1 — Pitch deck  (~1:20)  [show each slide as you speak]

**Slide 1 — Title.**
"Hi, we're Angawatch — greenhouse intelligence that protects a farmer's harvest before disease
can take it."

**Slides 2–3 — The problem / why it matters.**
"Most small and medium greenhouse farmers still check crop health by hand, walking the rows —
so problems are caught late, and that's costly. Around **40 percent** of global production is
lost to pre-harvest crop failures, and here in Kenya nearly **half of greenhouses** become
non-functional or badly degraded from disease, poor monitoring and poor environmental control."

**Slide 4 — Root cause.**
"It's a chain: no real-time monitoring, so environmental changes go undetected, leading to crop
stress and disease — and finally reduced yield and real financial loss."

**Slide 5 — Solution (Sense · Process · Alert).**
"Angawatch breaks that chain in three steps. **Sense** — solar-powered sensor nodes read
temperature, humidity and soil moisture and send live data on low power. **Process** — the
system watches for the exact humidity and heat that cause blight. **Alert** — the farmer gets a
message with the problem and the fix, over the mobile network, so no internet is needed."

**Slide 6 — Unique value.**
"Our value is simple: continuous monitoring and instant, actionable alerts that prevent losses
before they happen — without the cost and complexity of existing smart-farming systems."

---

## PART 2 — Live demo: both user flows  (~1:35)

**Bridge** (~5s): "Now the working product. It has two users — the **farmer**, and the
**cooperative** that finances and buys from them. Let me show both flows."

### User 1 — the Farmer  (~40s)
**SHOW:** Farm tab → click **Inject blight event** → the phone WhatsApp message.
"First, the farmer. Sensors stream into the system. I'll stage a blight event — [click] — it's
caught early and the farmer instantly gets this on a basic phone: *'high blight risk — ventilate
at dawn and spray.'* Simple, and in time to act."
**SHOW:** Feature phone tab → tap **Advice** → the SMS reply.
"And the farmer can text back — *ADVICE* — and get the full plan over SMS, in English or
Kiswahili. No smartphone, no internet."

### User 2 — the Cooperative / agronomist  (~50s)
**SHOW:** Co-op triage tab → the portfolio table (ranked by priority).
"Second, the cooperative — the off-taker that buys from hundreds of these farms but has only a
few field officers. It hires our advisory agent to triage every greenhouse — here's the
portfolio, ranked by which farms need a visit today."
**SHOW:** pick a farm → the advisory report (diagnosis + ranked plan).
"For any farm, the agent produces a verified report: the diagnosis, and a treatment plan ranked
by what works, what's safe for bees, and what's affordable."
**SHOW:** Crop doctor tab → the traversal path + Cypher (briefly).
"And the brain behind it is a **Neo4j knowledge graph** — the agent diagnoses by traversing it,
from the sensor readings to the disease to the treatment, and it shows its reasoning. A co-op
agronomist approves before anyone sprays."

### Close  (~10s)
**SHOW:** Farm tab → the Baba Neema pilot card.
"This already works in the field — one farmer, Baba Neema in Nakuru, got a warning two days
early and saved a crop he'd have lost half of. Angawatch — protecting harvests, and the income
that depends on them. Thank you."

---

## Tips
- The deck (farmer + sensors + SMS) is the foundation; the demo adds the depth — the farmer
  flow *proves* the deck, the co-op flow shows the business model + scale, the Neo4j moment
  covers the graph track.
- 3 min is a hard cap — speak briskly; if long, trim the bees/affordable detail in the report beat.
- Show both user flows clearly and label them on screen ("User 1: Farmer" / "User 2: Cooperative").
