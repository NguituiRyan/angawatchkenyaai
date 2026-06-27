# Masumi demo video — recording script (5–7 min)

Follows the Masumi recommended flow: ~1 min problem/user · ~1 min workflow/pain ·
~2.5 min agent demo · ~1 min Masumi role · ~1 min value/next steps. English narration.

---

## Before you hit record (checklist)
- [ ] **Reboot the deployed app** with the latest Streamlit secrets (Sokosumi key + advisory tx + agent id) so everything is live and current.
- [ ] **WhatsApp ready:** from the farmer phone, send the join word to the Twilio sandbox **within the last 24 h** (re-opens the session window). Record **early in the day** — the trial cap is **50 messages/day**; don't burn it beforehand.
- [ ] **Warm the app:** click through once (Neo4j connects, first LLM call) so it's snappy on camera. Then sidebar → **↺ Reset demo** for a clean start.
- [ ] **Open a second browser tab** on the real on-chain tx: `https://preprod.cardanoscan.io/transaction/d7c8c82b7c74aac960daf20f7d4ce1f17278332e4753c4453b423412b5f6aca8`
- [ ] **Phone visible** — screen-mirror or hold it to the webcam for the WhatsApp moment. (Fallback: the dashboard's alert card shows the exact message, and you can show a prior WhatsApp screenshot — so the take never stalls if a send is capped.)
- [ ] **Recorder:** OBS or Loom, 1080p. Add a small on-screen text overlay for each LIVE/MOCK label (list at the bottom).

---

## The script  (SHOW = on screen · SAY = what you say)

### 0:00–0:12 — Title
**SHOW:** Deployed app header "🌱 Greenhouse Monitoring", or a title card.
**SAY:** "This is Angawatch — a crop-health advisory agent that a farming cooperative can hire, pay, and audit through Masumi. I'll show the problem, the agent doing real work, and exactly where Masumi fits."

### 0:12–1:10 — Problem & user
**SHOW:** Farm tab (the hero conditions card + the farm graph).
**SAY:** "Our buyer is a horticulture cooperative — an off-taker that aggregates tomato from hundreds of contracted smallholder greenhouses, but employs only a handful of field officers. The problem: late blight and the Tuta pest spread in 24 to 48 hours, but officers visit on a fixed fortnightly rota and diagnose by eye. So they reach an infected farm days — even weeks — late, after 20 to 40 percent of that crop is already gone. For the co-op that means lost supply, missed grade-A volume, and broken delivery contracts."

### 1:10–2:00 — Current manual workflow & pain
**SHOW:** Sidebar "Live status" pills (Graph · neo4j, Alerts · live, LLM · live); slowly scroll the farm-record graph.
**SAY:** "Today it's all manual. Officers drive a rota, mostly visiting healthy farms. Farmers phone in only once they already see damage — too late. And the right product and pre-harvest interval are guesswork. Three officers cannot cover four hundred farms this way — and that gap is measured in tonnes of grade-A tomato lost every season. Everything I'm about to show is running live: a real Neo4j graph, a real LLM, real WhatsApp."

### 2:00–2:45 — Agent demo (1): the early, real alert
**SHOW:** Farm tab → click **Inject blight event**. The alert card appears ("📲 The farmer instantly receives this WhatsApp/SMS…"). Cut to the **phone** showing the WhatsApp message.
**SAY:** "Each greenhouse streams temperature, humidity, leaf-wetness, soil and pest-trap data into the graph. I'll stage a blight event. [click] The risk engine catches it early — and the farmer instantly gets a WhatsApp, in plain language, telling them what to do: 'high blight risk, ventilate at dawn and spray.' That's live, on a real phone, via Twilio — and it's bilingual, English or Kiswahili, so it works on a basic phone."
**OVERLAY:** `LIVE · Twilio WhatsApp`

### 2:45–3:40 — Agent demo (2): the agent reasons (this is the "work")
**SHOW:** Crop doctor tab → **Explain my latest alert**. Point at the path chain (Alert → Disease → Pathogen → Treatment) and the "graph evidence" condition chips; scroll the ranked treatment cards; open the **"Shows thinking — the Cypher traversal"** expander. Then in **Ask the agent**, type *"What's my main risk and the cheapest safe treatment?"* → **Run the agent** → point at the **decision trace** (the tools it chose).
**SAY:** "But this is an agent, not an alarm — it does real work. It diagnoses by traversing an agronomic knowledge graph: sensor readings, to the microclimate conditions they indicate, to the disease, to the pathogen — and it ranks treatments by efficacy, pre-harvest interval and cost, with a bee-safety check. And it's transparent — here's the exact graph path and the Cypher it ran. I can even ask it a question, and watch it *choose* which graph tools to run, step by step. That's the agent thinking — not a canned reply."
**OVERLAY:** `LIVE · Neo4j GraphRAG`

### 3:40–4:30 — Agent demo (3): the buyer's view + human approval
**SHOW:** Co-op triage tab → the **portfolio table** ranked by visit priority (point at "Visit now — within 24h"). Pick a farm → the **advisory report**: diagnosis, pathogen, risk, priority, the **SENSOR → CONSTRAINT → ACTION** banner, the ranked plan.
**SAY:** "Now the cooperative's view. The agent monitors every greenhouse and triages the whole portfolio — so three officers visit the handful of farms that need them *today*, by exception, not by rota. For any farm it produces a verified report: the diagnosis, the sensor reason the treatment window is open now, and the ranked plan. A co-op agronomist approves before anyone sprays — human in the loop, always."

### 4:30–5:40 — Masumi role
**SHOW:** Co-op tab → **Pay & deliver via Masumi** → the 5-step stepper plays. Switch to the **cardanoscan** browser tab (the real tx + metadata). Back to the app → **Run agent-to-agent** (the AgroInput Price Agent stepper). Scroll to the **Sokosumi panel** (LIVE · 20 coworkers discoverable + our coworker card).
**SAY:** "Here's where Masumi does real work. The co-op discovers the agent by its Cardano DID, pays per report into escrow, and the agent delivers. The result hash — the diagnosis and plan — is committed on-chain. This is a real Cardano preprod transaction; here it is on cardanoscan with our metadata. Then the agent itself becomes a buyer: it hires a *second* agent over Masumi — an input-price agent — to source the product price. That's agent-to-agent coordination. And our agent is a Sokosumi coworker — this is a live call to the Sokosumi marketplace: twenty coworkers discoverable right now, with ours ready to list. To be transparent: the escrow click-through runs a clearly-labeled mock; the on-chain audit you just saw is real."
**OVERLAY:** `LIVE · Cardano preprod tx` → `Agent-to-agent (Masumi)` → `LIVE · Sokosumi marketplace` → `escrow click-through = labeled mock`

### 5:40–6:40 — Business value, pilot, next steps
**SHOW:** Farm tab → the **Baba Neema pilot quote** card. End on the sidebar "Demo flow" or a closing card.
**SAY:** "The value: officers reallocated from rota to exception, outbreaks caught in hours instead of weeks, more grade-A volume delivered — and on our model a six-figure-shilling seasonal saving against a few-shilling per-report fee. And it's field-tested: before the co-op feature, we put one node in a real farmer's greenhouse — Baba Neema, in Nakuru. It warned him two days before he saw any spots; he sprayed in time and saved a crop he'd have lost half of — and asked for it on his second tunnel. Next we list on Sokosumi and onboard the first cooperative. Everything you saw is live except the escrow click-through; the on-chain proof is real. Thanks for watching."

---

## On-screen LIVE / MOCK overlays (add as text)
| When | Overlay text |
|---|---|
| Inject blight → WhatsApp | `LIVE · Twilio WhatsApp` |
| Crop doctor traversal | `LIVE · Neo4j Aura · GraphRAG` |
| Masumi round-trip | `Escrow round-trip = labeled MOCK` |
| Cardanoscan tx | `LIVE · real Cardano preprod tx` |
| Agent-to-agent | `Agent-to-agent over Masumi` |
| Sokosumi panel | `LIVE · Sokosumi marketplace (GET /v1/agents)` |
| LLM narration | `LLM narrates only · graph does the diagnosis` |

## Tips
- Speak slowly; pause on each click so the viewer follows.
- If a WhatsApp send is capped mid-take, keep narrating over the dashboard alert card and show a prior WhatsApp screenshot — don't stop.
- Keep it 5–7 min. To hit ~5 min, trim segment 1→2 to one combined minute and shorten segment 3b.
- Name the rubric words out loud at least once each: *buyer, measurable pain, the agent's work, human approves, Masumi pays + audits on-chain, business value.*
