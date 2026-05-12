# SPDX-FileCopyrightText: 2024-present Olostep <info@olostep.com>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from haystack.utils import Secret
from olostep.errors import OlostepServerError_AuthFailed

from olostep_haystack.fetcher import OlostepFetcher, OlostepFetcherError


class TestOlostepFetcher:
    def test_run_returns_documents(self):
        mock_client = MagicMock()
        mock_scrape_result = MagicMock()
        mock_content = MagicMock()
        mock_content.markdown_content = "# Hello World"
        mock_scrape_result.retrieve.return_value = mock_content
        mock_client.scrape.return_value = mock_scrape_result

        with patch("olostep.SyncOlostepClient", return_value=mock_client, create=True):
            fetcher = OlostepFetcher(api_key=Secret.from_token("test-key"))
            result = fetcher.run(urls=["https://example.com"])

        assert len(result["documents"]) == 1
        assert result["documents"][0].content == "# Hello World"
        assert result["documents"][0].meta["url"] == "https://example.com"

    def test_run_empty_content_logs_warning(self, caplog):
        mock_client = MagicMock()
        mock_scrape_result = MagicMock()
        mock_content = MagicMock()
        mock_content.markdown_content = None
        mock_scrape_result.retrieve.return_value = mock_content
        mock_client.scrape.return_value = mock_scrape_result

        with patch("olostep.SyncOlostepClient", return_value=mock_client, create=True):
            fetcher = OlostepFetcher(api_key=Secret.from_token("test-key"))
            with caplog.at_level(logging.WARNING, logger="olostep_haystack.fetcher"):
                result = fetcher.run(urls=["https://example.com"])

        assert result["documents"] == []
        assert "Olostep returned no markdown content for https://example.com" in caplog.text

    def test_auth_error_raises(self):
        mock_client = MagicMock()
        mock_client.scrape.side_effect = OlostepServerError_AuthFailed("auth failed")

        with patch("olostep.SyncOlostepClient", return_value=mock_client, create=True):
            fetcher = OlostepFetcher(api_key=Secret.from_token("test-key"))
            with pytest.raises(OlostepFetcherError, match="authentication failed"):
                fetcher.run(urls=["https://example.com"])

    def test_to_dict_from_dict_round_trip(self, monkeypatch):
        monkeypatch.setenv("OLOSTEP_API_KEY", "test-key")
        fetcher = OlostepFetcher(api_key=Secret.from_env_var("OLOSTEP_API_KEY"), format="markdown")

        data = fetcher.to_dict()
        restored = OlostepFetcher.from_dict(data)

        assert restored.format == "markdown"
        assert restored.api_key.resolve_value() == "test-key"

    @pytest.mark.skipif(
        not os.environ.get("OLOSTEP_API_KEY"),
        reason="Export OLOSTEP_API_KEY to run integration tests.",
    )
    @pytest.mark.integration
    def test_run_integration(self):
        fetcher = OlostepFetcher(api_key=Secret.from_env_var("OLOSTEP_API_KEY"), format="markdown")
        result = fetcher.run(urls=["https://example.com"])
        assert len(result["documents"]) > 0
