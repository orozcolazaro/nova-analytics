import pytest
from scraper.ats.base import ATSClient


def test_ats_client_is_abstract():
    with pytest.raises(TypeError):
        ATSClient()  # cannot instantiate abstract


def test_ats_client_subclass_must_implement_fetch():
    class Bad(ATSClient):
        provider = "x"
    with pytest.raises(TypeError):
        Bad()
