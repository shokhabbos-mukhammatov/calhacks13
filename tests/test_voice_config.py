"""Which hardening level a phone call runs at, on the ap-practice-target Actor.

Cartesia's tool sends only the caller's words and a call id, so the Actor
picks the config. It used to fall through to plain `baseline`, which does not
offer verify_vendor: the page promised CRS "while you are on the line" and no
call could ever reach it.
"""
import importlib.util
from pathlib import Path

import pytest

from firedrill.drill import make_config
from firedrill.verify import NoPhoneOwner, NoSenderCheck, RdapDomainAge, VendorVerifier

MAIN = Path(__file__).resolve().parents[1] / "actors" / "victim-standby" / "src" / "main.py"


@pytest.fixture(scope="module")
def target():
    spec = importlib.util.spec_from_file_location("target_main", MAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_call_offers_crs_by_default(target):
    name = target.voice_config({}, {})
    verifier = VendorVerifier(RdapDomainAge(), NoSenderCheck(), NoPhoneOwner())
    assert make_config(name, model=None, verifier=verifier).verifier is not None


def test_a_call_is_still_breakable_by_default(target):
    # CRS is evidence the agent may use, not a control: no policy, no gates.
    config = make_config(target.voice_config({}, {}), model=None)
    assert not config.tool_scope


def test_the_actor_setting_overrides_the_default(target):
    assert target.voice_config({}, {"VOICE_CONFIG": "baseline"}) == "baseline"


def test_a_caller_naming_a_config_wins(target):
    assert target.voice_config({"config": "patch:v3"}, {"VOICE_CONFIG": "baseline"}) == "patch:v3"


def test_a_bad_setting_falls_back_instead_of_failing_every_call(target):
    assert target.voice_config({}, {"VOICE_CONFIG": "patch:does-not-exist"}) == target.DEFAULT_VOICE_CONFIG
    assert target.voice_config({}, {"VOICE_CONFIG": "nonsense"}) == target.DEFAULT_VOICE_CONFIG
