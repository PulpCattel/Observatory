"""
Test settings creation and handling
"""
from bobs.obs.filters import Include, Equal, Greater
from bobs.settings import Settings
from marshmallow import ValidationError
from pytest import raises
from toml import loads


def test_settings():
    """
    Test Settings Model
    """
    settings = Settings.from_default()
    assert settings['general']['logging'] == 'warning'
    assert settings['limits']['concurrency_limit'] == 3
    assert settings['limits']['memory_limit'] == 80
    assert settings['network']['endpoint'] == "http://127.0.0.1:8332"
    assert settings['scan']['force'] is False
    assert settings['filtering']['match_all'] is False
    assert settings['filters']['coinbase'] == {'is_coinbase': Equal(True)}
    assert settings['filters']['txid'] == {'txid': Include('')}
    assert settings['filters']['address'] == {'addresses': Include('')}
    assert settings['filters']['huge_vsize'] == {'vsize': Greater(50000)}


def test_malformed():
    """
    Test Settings Model correctly catches malformed TOML configuration file
    """
    malformed_toml = """[general]
    logging = 'warning'"""
    with raises(ValidationError):
        Settings().load(loads(malformed_toml))
