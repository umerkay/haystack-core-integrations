# SPDX-FileCopyrightText: 2024-present Olostep <info@olostep.com>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from haystack import Document, component, default_from_dict, default_to_dict
from haystack.utils import Secret, deserialize_secrets_inplace

logger = logging.getLogger(__name__)


class OlostepFetcherError(Exception):
    """Raised when Olostep fetching fails."""


@component
class OlostepFetcher:
    """
    Fetch and convert web pages to Markdown using Olostep's scrape API.

    Uses SyncOlostepClient (the current Olostep Python SDK).
    Do NOT use the legacy Olostep class with client.scrapes.create().

    Usage:
        from olostep_haystack import OlostepFetcher
        fetcher = OlostepFetcher(api_key=Secret.from_env_var("OLOSTEP_API_KEY"))
        result = fetcher.run(urls=["https://example.com"])
        # result["documents"] -> List[Document]
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var("OLOSTEP_API_KEY"),
        format: str = "markdown",  # noqa: A002
    ) -> None:
        if format not in ("markdown", "html"):
            msg = "format must be 'markdown' or 'html'"
            raise ValueError(msg)
        self.api_key = api_key
        self.format = format

    @component.output_types(documents=list[Document])
    def run(self, urls: list[str]) -> dict[str, Any]:
        """
        Fetch one or more URLs and return their content as Documents.

        :param urls: list of URLs to scrape
        :returns: dict with 'documents' (List[Document])
        :raises OlostepFetcherError: on API failure
        """
        from olostep import SyncOlostepClient  # noqa: PLC0415
        from olostep.errors import Olostep_BaseError, OlostepServerError_AuthFailed  # noqa: PLC0415

        resolved_key = self.api_key.resolve_value()
        if not resolved_key:
            msg = "OLOSTEP_API_KEY is not set. Set it in your environment or pass it explicitly."
            raise OlostepFetcherError(msg)

        client = SyncOlostepClient(api_key=resolved_key)
        documents: list[Document] = []

        for url in urls:
            try:
                scrape_result = client.scrape(url)
                content_obj = scrape_result.retrieve([self.format])
                content = content_obj.markdown_content if self.format == "markdown" else content_obj.html_content
                if content:
                    documents.append(Document(content=content, meta={"url": url}))
                else:
                    logger.warning("Olostep returned no %s content for %s", self.format, url)
            except OlostepServerError_AuthFailed as e:
                msg = "Olostep authentication failed — check your API key."
                raise OlostepFetcherError(msg) from e
            except Olostep_BaseError as e:
                logger.warning("Olostep error for %s: %s", url, e)

        return {"documents": documents}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the component to a dictionary."""
        return default_to_dict(
            self,
            api_key=self.api_key.to_dict(),
            format=self.format,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OlostepFetcher":
        """Deserialize a component from a dictionary."""
        deserialize_secrets_inplace(data["init_parameters"], keys=["api_key"])
        return default_from_dict(cls, data)
