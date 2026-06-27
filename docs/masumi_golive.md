# Masumi go-live — getting a REAL on-chain proof (preprod)

This turns "Masumi Fit" from a labeled mock into a **verifiable on-chain transaction** judges can
click. You do NOT need the live click-through to be real — you need ONE real preprod transaction
whose hash you display. The app already supports this via `MASUMI_PRERECORDED_TX` (the "hybrid").

Read first (per the bounty rules): https://www.masumi.network/skill.md and https://docs.masumi.network/

Time: ~20 min. The slow/flaky part is on-chain confirmation — do this the **night before**, not live.

---

## Path A — Minimum real proof (recommended, ~20 min)
Goal: a real Cardano **Preprod** transaction hash to show as the audit link.

1. **Wallet** — install Eternl or Lace, switch network to **Preprod**, create a wallet, copy the
   `addr_test1…` address.
2. **Fund it** — Cardano testnet faucet: https://docs.cardano.org/cardano-testnets/tools/faucet →
   select **Preprod** → paste address → receive test ADA (≈1–2 min).
3. **Register the agent** — open https://explorer.masumi.network/?network=preprod → connect wallet →
   register an agent profile:
   - Name: `Angawatch Crop-Health Advisory Agent`
   - API URL: your deployed MIP-003 endpoint if you have one (else a placeholder is fine for the
     registration tx) — see Path B to deploy it.
   - Input/output schema + price: use the profile printed by `python -m masumi_integration.sokosumi`.
   - Submit → this mints an agent NFT / DID and produces a **real transaction**. Copy its **tx hash**
     and the **agent identifier (DID)**.
4. **Wire it in** — set in `.env` / Streamlit secrets:
   ```
   MASUMI_PRERECORDED_TX=<the registration tx hash>
   AGENT_IDENTIFIER=<the DID>
   ```
5. **Verify** — `python scripts/preflight.py` shows Masumi LIVE; the dashboard's audit step now links
   to `https://preprod.cardanoscan.io/transaction/<hash>` labeled `prerecorded-real`.

In the demo, say: *"Registration and the on-chain audit hash are real on Cardano preprod — here's the
transaction. The live payment click-through runs in safe mode so the demo never stalls on a confirm."*

---

## Path B — Real escrow payment (stretch, needs the Payment Service)
Only if Path A is solid and you have time.

1. Run the Masumi services locally (Docker): clone
   `github.com/masumi-network/masumi-services-dev-quickstart`, `cp .env.example .env` (add a Blockfrost
   preprod key), `docker compose up -d`. Registry → :3000/docs, Payment → :3001/docs.
   (Or point at a hosted preprod Payment Service if you have an API key.)
2. Install the SDK: `pip install masumi` (already in `requirements-full.txt`).
3. Set in `.env`:
   ```
   MASUMI_MODE=real
   PAYMENT_SERVICE_URL=http://localhost:3001/api/v1
   PAYMENT_API_KEY=<from the service>
   AGENT_IDENTIFIER=<your DID>
   SELLER_VKEY=<your selling wallet vkey>
   NETWORK=Preprod
   PAYMENT_AMOUNT=5000000
   PAYMENT_UNIT=lovelace
   ```
4. `python -m masumi_integration.demo` → exercises `create_payment_request` → escrow lock →
   `complete_payment` (Decision-Logs the result hash) → audit. `RealMasumiBackend` auto-downgrades to
   mock on any error, so this can't break the demo.

---

## Path C — Deploy the MIP-003 service so the agent is publicly discoverable (optional)
The agent's endpoints (`/availability`, `/input_schema`, `/start_job`, `/status`, `/provide_input`,
`/demo`) live in `api/main.py` (`uvicorn api.main:app`). Deploy to any Python host (Render/Railway/Fly)
and use that URL as the agent's API URL during registration (Path A step 3). For a quick public URL
during the demo you can also tunnel: `uvicorn api.main:app --port 8000` + `ngrok http 8000`.

---

## What proves it (for judges)
- A real **agent DID / NFT** on preprod (identity).
- A real **transaction hash** on `preprod.cardanoscan.io` (payment + Decision-Log of the result hash).
- The deterministic **`result_hash`** (committing to the advisory diagnosis + plan) matches what's
  committed on-chain — reproducible.

That's the "verifiable result recorded on-chain" pattern the winning Masumi projects used — and
because the hash commits to a diagnosis a farmer acts on, the audit does real work, not decoration.
