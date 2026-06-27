# Main presentation video — Mercy Corps AgriFin track (≤3 min)

Reused for AgriFin + Neo4j + Masumi. Leads with the financial stakes, shows the live
product + the Neo4j graph reasoning, closes on real-farmer impact. ~420 words ≈ 2:50.

## Before you record
- [ ] Reboot the deployed app with the latest secrets (so the demo is current + Neo4j live).
- [ ] WhatsApp: from the farmer phone, re-send the sandbox join word within 24 h; record early
      (trial cap = 50 msgs/day). Phone visible for the alert shot. Fallback: the dashboard
      alert card shows the exact message + a prior WhatsApp screenshot.
- [ ] Warm the app once, then sidebar → ↺ Reset demo.

---

## Script  (SHOW = on screen · SAY = narration)

### 0:00–0:25 — The problem (the AgriFin stakes)
**SHOW:** Farm tab (hero) / a greenhouse image.
**SAY:** "In Kenya, a smallholder tomato farmer can lose 20 to 40 percent of a crop to disease
in a single week — before they even see it on the leaves. That lost crop is lost income, and an
input loan they now can't repay. For the cooperatives and off-takers who finance and buy from
them, it's broken supply. Crop disease is one of the biggest income shocks in smallholder
agriculture — and today it's caught far too late."

### 0:25–0:50 — The solution
**SHOW:** The dashboard overview / the farm-record graph.
**SAY:** "We built Angawatch. It turns a greenhouse into an early-warning and advisory system.
Sensors stream the microclimate into a Neo4j knowledge graph — and the moment conditions turn
dangerous, the farmer gets a simple WhatsApp telling them exactly what to do, in time to save
the crop. Every reading, alert and action becomes a verified farm record a cooperative — and a
lender — can trust."

### 0:50–1:25 — Demo 1: the crop-saving alert
**SHOW:** Farm tab → click **Inject blight event** → the phone WhatsApp message.
**SAY:** "Here's the live system. I'll stage a blight event. [click] The risk engine catches it
early — and the farmer instantly gets this WhatsApp: 'high blight risk — ventilate at dawn and
spray.' Plain language, on a real phone, in English or Kiswahili. That's a crop, and an income,
saved."

### 1:25–2:05 — Demo 2: the agent + the Neo4j graph (the intelligence)
**SHOW:** Crop doctor tab → **Explain my latest alert** → the traversal path + ranked treatment
cards (open the Cypher expander briefly).
**SAY:** "But it's more than an alarm. Our advisory agent diagnoses the problem by traversing the
knowledge graph — from the sensor readings, to the microclimate, to the disease and its cause —
and returns a treatment plan ranked by what works, what's safe for bees, and what's affordable,
within the pre-harvest interval. And it shows its reasoning — the exact path it walked."

### 2:05–2:30 — Demo 3: who pays (the AgriFin model)
**SHOW:** Co-op triage tab → the portfolio table → a verified advisory report.
**SAY:** "And this is who pays for it. A cooperative with hundreds of contracted greenhouses but
only a handful of field officers hires the agent to triage every farm — so an officer visits the
five that need them today, not on a two-week rota. A co-op agronomist approves before anyone
sprays — the agent recommends, a human decides."

### 2:30–3:00 — Impact, pilot, close
**SHOW:** Farm tab → the Baba Neema pilot quote card.
**SAY:** "And it's field-tested. Before the cooperative feature, we put one node in a real
farmer's greenhouse — Baba Neema, in Nakuru. It warned him two days before he saw any spots; he
sprayed in time and saved a crop he'd have lost half of — and asked for it on his second tunnel.
Multiply that across a cooperative: income protected, loans repaid, grade-A volume delivered.
Farmers get the warning free; the cooperative pays per farm it protects. Angawatch — catching
crop disease before it spreads, and protecting the income that smallholder finance depends on.
Thank you."

---

## Tips
- 3 minutes is tight — speak briskly, don't pause long; cut a sentence from 0:25–0:50 if you run over.
- The Neo4j graph moment (Crop doctor traversal) earns the Neo4j-track reuse — make sure it's on screen.
- Say the money words at least once: **income, input loan, repay, cooperative finance, supply.**
