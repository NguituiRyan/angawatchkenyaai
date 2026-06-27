"""Africa's Talking SMS channel + multi-channel dispatch (WhatsApp + SMS). All mocked."""
import os

os.environ["GRAPH_BACKEND"] = "memory"

from types import SimpleNamespace  # noqa: E402

from alerts.africas_talking_channel import AfricasTalkingChannel, _sms_safe  # noqa: E402
from alerts.channel import Alert, DeliveryResult  # noqa: E402
from alerts.dispatcher import MultiChannel, build_channel  # noqa: E402


def _alert():
    return Alert(gh_id="gh-001", kind="late_blight", level="HIGH",
                 message="⚠️ Angawatch · gh-001: HIGH blight risk. Do now: spray. Reply ADVICE.",
                 ts="t", reason="r")


def _st(**kw):
    base = dict(AT_USERNAME="sandbox", AT_API_KEY="key", AT_SENDER_ID=None, AT_SANDBOX=True,
                FARMER_PHONE="+254700000000")
    base.update(kw)
    return SimpleNamespace(**base)


class _Resp:
    def __init__(self, recips):
        self._r = recips

    def raise_for_status(self):
        pass

    def json(self):
        return {"SMSMessageData": {"Message": "Sent to 1/1", "Recipients": self._r}}


def test_sms_safe_strips_non_gsm():
    out = _sms_safe("⚠️ Angawatch · gh-001 → spray")
    assert "⚠️" not in out and "·" not in out and "->" in out


def test_at_channel_success(monkeypatch):
    import requests
    monkeypatch.setattr(requests, "post", lambda *a, **k: _Resp(
        [{"status": "Success", "messageId": "ATXid_1", "cost": "KES 0.8"}]))
    res = AfricasTalkingChannel(_st()).send("+254700000000", _alert())
    assert res.ok and res.mode == "live" and res.provider == "sms" and "ATXid_1" in res.detail


def test_at_channel_failure_falls_back_to_console(monkeypatch):
    import requests

    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(requests, "post", boom)
    res = AfricasTalkingChannel(_st()).send("+254700000000", _alert())
    assert res.mode == "mock"          # graceful console fallback, never raises


def test_multichannel_reports_all_live_providers():
    class Fake:
        mode = "live"

        def __init__(self, p):
            self.p = p

        def send(self, to, a):
            return DeliveryResult(True, "live", self.p, "ok")

    r = MultiChannel([Fake("whatsapp"), Fake("sms")]).send("+254700000000", _alert())
    assert r.mode == "live" and "whatsapp" in r.provider and "sms" in r.provider


def test_build_channel_picks_at_when_only_at_configured():
    s = _st()
    s.alert_mode = lambda: "mock"      # no Twilio
    s.at_mode = lambda: "live"         # Africa's Talking configured
    assert isinstance(build_channel(s), AfricasTalkingChannel)


def test_build_channel_multi_when_both_configured():
    s = _st(TWILIO_SID="x", TWILIO_TOKEN="y", TWILIO_FROM="whatsapp:+1", TWILIO_SMS_FROM=None)
    s.alert_mode = lambda: "live"
    s.at_mode = lambda: "live"
    assert isinstance(build_channel(s), MultiChannel)
