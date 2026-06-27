# Neo4j technical proof video — script (≤2 min, Loom)

Record a **real screen recording** of **Neo4j Workspace or Neo4j Browser** connected to your
live Aura instance. No slides/screenshots/mockups. **Do not show the password / connection
string / credentials** — connect first, then start recording on the query screen.

Open Aura → your instance → **Open with Workspace** (or Browser) → use the **Query** panel.

---

### Step 1 — Show the graph map (~30s)
Paste and run:
```cypher
CALL db.schema.visualization()
```
**Say:** "This is our live Neo4j Aura graph schema. You can see the farm record — Greenhouse,
Reading, Alert, Season, Harvest — joined to the agronomic knowledge graph — Disease, Pathogen,
Condition, Treatment, Pest. These labels and relationship types match our integration document."
→ Hover over a couple of nodes and relationships so the labels (e.g. `Disease`, `CONTROLS`,
`INDICATES`) are visible.

### Step 2 — Run the official count query (~20s)
Paste and run **exactly**:
```cypher
MATCH (n)
WITH count(n) AS Nodes
OPTIONAL MATCH ()-[r]->()
RETURN Nodes, count(r) AS Relationships;
```
**Say:** "Our graph has roughly 793 nodes and 2,200 relationships — both well above zero."
→ Make sure the two numbers are clearly on screen. (Whatever it returns is fine; both must be > 0.)

### Step 3 — Show one product-relevant query (~50s)
This is the GraphRAG traversal that powers the advisory. Run the **graph-rendering** version so
Neo4j Browser/Workspace draws the subgraph on screen:
```cypher
MATCH (g:Greenhouse {id:'gh-001'})-[:RAISED]->(a:Alert)-[:FOR_DISEASE]->(d:Disease)-[:CAUSED_BY]->(p:Pathogen)
MATCH (d)<-[c:CONTROLS]-(t:Treatment)
RETURN g, a, d, p, c, t LIMIT 30;
```
**Say:** "This is the query behind our advisory. Starting from a greenhouse's blight alert, it
traverses to the disease — Late blight — to its pathogen — Phytophthora infestans — and out to
every treatment that controls it. This multi-hop reasoning is what produces the ranked,
pre-harvest-interval-aware treatment plan in our app."

**(Optional, if time)** Show that live sensor readings drive the diagnosis — run the table version:
```cypher
MATCH (g:Greenhouse {id:'gh-001'})-[:RECORDED]->(rd:Reading)-[:INDICATES]->(c:Condition)<-[:FAVORS_REVERSE]-(d:Disease)
RETURN c.name AS condition, collect(DISTINCT d.name) AS likely_diseases, count(DISTINCT rd) AS supporting_readings
ORDER BY supporting_readings DESC LIMIT 4;
```
**Say:** "And this shows the diagnosis being driven by real sensor data — each microclimate
condition, the diseases it favours, and how many sensor readings support it."

---

**Tips:** keep it under 2 minutes; zoom the browser in (Ctrl/Cmd +) so text is legible; pause a
beat on each result; the labels you show must match the Neo4j Integration Document.
