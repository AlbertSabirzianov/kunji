import base64
import json
import time

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from kunji import checkin
from kunji.config import Config


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def make_signer(monkeypatch):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    monkeypatch.setenv("KUNJI_DEV", "1")
    monkeypatch.setenv("KUNJI_DEV_PUBLIC_KEY", base64.b64encode(pub).decode())

    def sign(payload: dict) -> dict:
        raw = json.dumps(payload).encode()
        return {"payload": b64url(raw), "sig": b64url(key.sign(raw))}

    return sign


def test_versions():
    assert checkin.is_newer("0.2.0", "0.1.9")
    assert not checkin.is_newer("0.1.0", "0.1.0")
    assert checkin.is_newer("1.0.0", "0.9.12")


def test_valid_signature(monkeypatch):
    sign = make_signer(monkeypatch)
    iid = checkin.install_id()
    blob = sign({"install_id": iid, "plan": "pro", "expires_at": time.time() + 60})
    assert checkin.verify_blob(blob, iid)["plan"] == "pro"


def test_tampered_expired_or_wrong_install(monkeypatch):
    sign = make_signer(monkeypatch)
    iid = checkin.install_id()
    blob = sign({"install_id": iid, "plan": "free", "expires_at": time.time() + 60})
    forged = json.dumps({"install_id": iid, "plan": "pro", "expires_at": time.time() + 60})
    assert checkin.verify_blob({**blob, "payload": b64url(forged.encode())}, iid) is None
    assert checkin.verify_blob(sign({"install_id": iid, "expires_at": 1}), iid) is None
    other = sign({"install_id": "someone-else", "expires_at": time.time() + 60})
    assert checkin.verify_blob(other, iid) is None


def test_no_trusted_keys_means_free(monkeypatch):
    monkeypatch.delenv("KUNJI_DEV", raising=False)
    blob = {"payload": b64url(b"{}"), "sig": b64url(b"x" * 64)}
    assert checkin.verify_blob(blob, "x") is None


def test_checkin_disabled_without_url():
    assert checkin.checkin(Config.load()).plan == "free"


def test_checkin_roundtrip_and_cache(monkeypatch):
    sign = make_signer(monkeypatch)
    sent = {}

    def handler(request):
        body = json.loads(request.content)
        sent.update(body)
        return httpx.Response(200, json=sign({
            "install_id": body["install_id"], "plan": "trial", "trial_ends": "2030-01-01",
            "min_version": "9.0.0", "expires_at": time.time() + 3600,
        }))

    cfg = Config.load()
    cfg.set("cloud.url", "https://cloud.example.com")
    ent = checkin.checkin(cfg, transport=httpx.MockTransport(handler))
    assert ent.plan == "trial" and ent.verified and ent.outdated
    assert set(sent) == {"install_id", "version", "os"}  # never keys or prompts
    assert checkin.load_entitlement().plan == "trial"  # cached + re-verified


def test_http_only_allowed_for_localhost():
    cfg = Config.load()
    cfg.set("cloud.url", "http://evil.example.com")
    assert checkin.checkin(cfg).verified is False
