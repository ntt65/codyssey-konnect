"""Offline JWT compatibility and failure categorization tests (no real Auth calls)."""
import asyncio
import time
from functools import lru_cache

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jose import jwk, jwt

from app.config import settings
from app.core import auth
from app.core.exceptions import AuthError, ConfigurationError, ExternalSourceError


@pytest.fixture
def jwt_setup(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    return {
        "sub": "user-id", "aud": "authenticated",
        "iss": "https://example.supabase.co/auth/v1", "exp": int(time.time()) + 300,
    }


def signed_token(monkeypatch, claims, algorithm="RS256"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048) if algorithm == "RS256" else ec.generate_private_key(ec.SECP256R1())
    private = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    public_jwk = jwk.construct(public, algorithm).to_dict()
    public_jwk["kid"] = "test-key"
    monkeypatch.setattr(auth, "_get_jwks", lru_cache()(lambda: {"keys": [public_jwk]}))
    return jwt.encode(claims, private, algorithm=algorithm, headers={"kid": "test-key"})


@pytest.mark.parametrize("algorithm", ["RS256", "ES256"])
def test_valid_asymmetric_token(monkeypatch, jwt_setup, algorithm):
    token = signed_token(monkeypatch, jwt_setup, algorithm)
    user = asyncio.run(auth.verify_token(token))
    assert user.id == "user-id"


@pytest.mark.parametrize("claim", ["aud", "iss", "exp", "sub"])
def test_required_claims_and_values(monkeypatch, jwt_setup, claim):
    jwt_setup.pop(claim)
    token = signed_token(monkeypatch, jwt_setup)
    with pytest.raises(AuthError):
        asyncio.run(auth.verify_token(token))


@pytest.mark.parametrize(("claim", "value"), [("aud", "other-app"), ("iss", "other-project"), ("exp", 1)])
def test_wrong_claims_rejected(monkeypatch, jwt_setup, claim, value):
    jwt_setup[claim] = value
    token = signed_token(monkeypatch, jwt_setup)
    with pytest.raises(AuthError):
        asyncio.run(auth.verify_token(token))


def test_unknown_kid_refreshes_once(monkeypatch, jwt_setup):
    token = signed_token(monkeypatch, jwt_setup)
    calls = []
    @lru_cache()
    def keys():
        calls.append(True)
        return {"keys": []}
    monkeypatch.setattr(auth, "_get_jwks", keys)
    with pytest.raises(AuthError, match="서명 키"):
        asyncio.run(auth.verify_token(token))
    assert len(calls) == 2


def test_jwks_timeout_is_service_failure_not_bad_login(monkeypatch, jwt_setup):
    auth._get_jwks.cache_clear()
    def fail(*args, **kwargs):
        raise httpx.ReadTimeout("TOP_SECRET")
    monkeypatch.setattr(auth.httpx, "get", fail)
    try:
        with pytest.raises(ExternalSourceError) as error:
            auth._get_jwks()
        assert "TOP_SECRET" not in str(error.value)
    finally:
        auth._get_jwks.cache_clear()


def test_missing_auth_config(monkeypatch):
    auth._get_jwks.cache_clear()
    monkeypatch.setattr(settings, "supabase_url", "")
    with pytest.raises(ConfigurationError, match="SUPABASE_URL"):
        auth._get_jwks()


def test_malformed_token_does_not_echo_it():
    with pytest.raises(AuthError) as error:
        asyncio.run(auth.verify_token("TOP_SECRET"))
    assert "TOP_SECRET" not in str(error.value)
