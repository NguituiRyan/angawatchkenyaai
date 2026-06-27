"""Central configuration for Angawatch.

ONE place loads `.env` (and, in Streamlit, `st.secrets` which dashboard/app.py
copies into the environment first). Every other module imports `get_settings()`.

Design rule: a missing credential is never fatal. Each `*_mode` helper resolves
to "live" or "mock" so the rest of the app can degrade gracefully and LABEL it.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Neo4j -------------------------------------------------------------
    NEO4J_URI: str | None = None
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str | None = None
    NEO4J_DATABASE: str = ""   # blank = use the instance's home/default database
    GRAPH_BACKEND: str = "auto"  # auto | neo4j | memory

    # --- OpenRouter LLM ----------------------------------------------------
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str = "openrouter/google/gemma-4-26b-a4b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODE: str = "auto"  # auto | live | mock

    # --- Twilio (WhatsApp) -------------------------------------------------
    TWILIO_SID: str | None = None
    TWILIO_TOKEN: str | None = None
    TWILIO_FROM: str = "whatsapp:+14155238886"
    TWILIO_SMS_FROM: str | None = None
    FARMER_PHONE: str | None = None

    # --- Africa's Talking (real Kenya SMS) ---------------------------------
    AT_USERNAME: str | None = None      # app username from africastalking.com (or "sandbox")
    AT_API_KEY: str | None = None       # Settings -> API Key
    AT_SENDER_ID: str | None = None     # optional registered sender ID / shortcode
    AT_SANDBOX: bool = False            # True -> sandbox (sends to the AT simulator, not a real phone)

    # --- Vision ------------------------------------------------------------
    VISION_MODE: str = "auto"  # auto | live | mock
    HF_MODEL_ID: str = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"

    # --- Masumi ------------------------------------------------------------
    MASUMI_MODE: str = "mock"  # real | mock
    NETWORK: str = "Preprod"
    PAYMENT_SERVICE_URL: str | None = None
    PAYMENT_API_KEY: str | None = None
    AGENT_IDENTIFIER: str | None = None
    SELLER_VKEY: str | None = None
    PAYMENT_AMOUNT: str = "5000000"
    PAYMENT_UNIT: str = "lovelace"
    MASUMI_PRERECORDED_TX: str | None = None

    # --- Sokosumi (marketplace; +10 bonus) --------------------------------
    # mainnet: https://api.sokosumi.com  ·  preprod: https://api.preprod.sokosumi.com
    SOKOSUMI_API_URL: str = "https://api.sokosumi.com"
    SOKOSUMI_API_KEY: str | None = None
    AGENT_API_URL: str = "https://angawatch.example/mip003"

    # --- Cardano on-chain Decision Logging (real audit proof) -------------
    BLOCKFROST_PROJECT_ID: str | None = None   # free preprod key from blockfrost.io
    CARDANO_WALLET_SKEY: str = "data/.preprod.skey"
    MASUMI_ONCHAIN_LIVE: bool = False          # commit a FRESH on-chain tx per round-trip

    # --- Demo identity -----------------------------------------------------
    DEFAULT_FARMER_ID: str = "Farmer-A"
    DEFAULT_GREENHOUSE_ID: str = "gh-001"

    # ----------------------------------------------------------------------
    # Effective-mode resolvers: "live" only when the integration *can* run.
    # ----------------------------------------------------------------------
    @property
    def neo4j_configured(self) -> bool:
        return bool(self.NEO4J_URI and self.NEO4J_PASSWORD)

    def graph_mode(self) -> str:
        if self.GRAPH_BACKEND == "memory":
            return "memory"
        if self.GRAPH_BACKEND == "neo4j":
            return "neo4j"
        return "neo4j" if self.neo4j_configured else "memory"

    def llm_mode(self) -> str:
        if self.LLM_MODE == "mock":
            return "mock"
        if self.LLM_MODE == "live":
            return "live"
        return "live" if self.OPENROUTER_API_KEY else "mock"

    def alert_mode(self) -> str:
        return "live" if (self.TWILIO_SID and self.TWILIO_TOKEN) else "mock"

    def at_mode(self) -> str:
        """Africa's Talking SMS: live when username + api key are present."""
        return "live" if (self.AT_USERNAME and self.AT_API_KEY) else "mock"

    def vision_mode(self) -> str:
        if self.VISION_MODE in ("live", "mock"):
            return self.VISION_MODE
        return "auto"  # classifier decides at load time (lazy import)

    def masumi_mode(self) -> str:
        if self.MASUMI_MODE == "real" and self.PAYMENT_API_KEY and self.PAYMENT_SERVICE_URL:
            return "real"
        return "mock"

    def masumi_status(self) -> str:
        """real = live escrow; hybrid = simulated round-trip + REAL on-chain proof; mock."""
        if self.masumi_mode() == "real":
            return "real"
        if self.MASUMI_PRERECORDED_TX:
            return "hybrid"
        return "mock"

    def sokosumi_mode(self) -> str:
        return "live" if self.SOKOSUMI_API_KEY else "mock"

    def onchain_live(self) -> bool:
        """Can we submit a fresh, real preprod Decision-Log tx this run?"""
        import os
        return bool(self.MASUMI_ONCHAIN_LIVE and self.BLOCKFROST_PROJECT_ID
                    and os.path.exists(self.CARDANO_WALLET_SKEY))


@lru_cache
def get_settings() -> Settings:
    return Settings()
