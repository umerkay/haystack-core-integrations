# SPDX-FileCopyrightText: 2024-present Olostep <info@olostep.com>
#
# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import MagicMock, patch

import pytest
from haystack import Document
from haystack.utils import Secret

from olostep_haystack.web_search import OlostepSearchError, OlostepWebSearch

MOCK_RESPONSE = {
    "result": {
        "links": [
            {"url": "https://example.com", "title": "Example", "description": "An example site"},
            {"url": "https://another.com", "title": "Another", "description": "Another site"},
        ]
    }
}


class TestOlostepWebSearch:
    def test_run_returns_documents_and_links(self):
        ws = OlostepWebSearch(api_key=Secret.from_token("test-key"), top_k=5)

        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_RESPONSE

        with patch("olostep_haystack.web_search.requests.post", return_value=mock_response):
            result = ws.run(query="test")

        assert len(result["documents"]) == 2
        assert isinstance(result["documents"][0], Document)
        assert result["documents"][0].content == "An example site"
        assert result["documents"][0].meta["title"] == "Example"
        assert result["documents"][0].meta["link"] == "https://example.com"
        assert result["links"] == ["https://example.com", "https://another.com"]

    def test_run_top_k_limits_results(self):
        ws = OlostepWebSearch(api_key=Secret.from_token("test-key"), top_k=1)

        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_RESPONSE

        with patch("olostep_haystack.web_search.requests.post", return_value=mock_response):
            result = ws.run(query="test")

        assert len(result["documents"]) == 1
        assert result["links"] == ["https://example.com"]

    def test_missing_api_key_raises(self):
        ws = OlostepWebSearch(api_key=Secret.from_env_var("OLOSTEP_API_KEY", strict=False))

        with pytest.raises(OlostepSearchError, match="OLOSTEP_API_KEY is not set"):
            ws.run(query="test")

    def test_to_dict_from_dict_round_trip(self, monkeypatch):
        monkeypatch.setenv("OLOSTEP_API_KEY", "test-key")
        ws = OlostepWebSearch(
            api_key=Secret.from_env_var("OLOSTEP_API_KEY"),
            top_k=3,
            allowed_domains=["example.com"],
            search_params={"foo": "bar"},
        )

        data = ws.to_dict()
        restored = OlostepWebSearch.from_dict(data)

        assert restored.top_k == 3
        assert restored.allowed_domains == ["example.com"]
        assert restored.search_params == {"foo": "bar"}
        assert restored.api_key.resolve_value() == "test-key"

    @pytest.mark.skipif(
        not os.environ.get("OLOSTEP_API_KEY"),
        reason="Export OLOSTEP_API_KEY to run integration tests.",
    )
    @pytest.mark.integration
    def test_run_integration(self):
        ws = OlostepWebSearch(api_key=Secret.from_env_var("OLOSTEP_API_KEY"), top_k=3)
        result = ws.run(query="What is Haystack by deepset?")
        assert len(result["documents"]) > 0
        assert len(result["links"]) > 0
        assert isinstance(result["documents"][0], Document)
