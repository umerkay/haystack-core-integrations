# SPDX-FileCopyrightText: 2024-present Olostep <info@olostep.com>
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

import requests
from haystack import Document, component, default_from_dict, default_to_dict
from haystack.utils import Secret, deserialize_secrets_inplace

logger = logging.getLogger(__name__)


class OlostepSearchError(Exception):
    """Raised when Olostep search fails."""


@component
class OlostepWebSearch:
    """
    Search the web using Olostep's /searches endpoint.

    Usage:
        from olostep_haystack import OlostepWebSearch
        search = OlostepWebSearch(api_key=Secret.from_env_var("OLOSTEP_API_KEY"))
        result = search.run(query="what is haystack?")
        # result["documents"] -> List[Document]
        # result["links"] -> List[str]
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var("OLOSTEP_API_KEY"),
        top_k: int = 5,
        allowed_domains: list[str] | None = None,
        search_params: dict[str, Any] | None = None,
    ) -> None:
        self.api_key = api_key
        self.top_k = top_k
        self.allowed_domains = allowed_domains or []
        self.search_params = search_params or {}

    @component.output_types(documents=list[Document], links=list[str])
    def run(self, query: str) -> dict[str, Any]:
        """
        Search the web using Olostep.

        :param query: the search query string
        :returns: dict with 'documents' (List[Document]) and 'links' (List[str])
        :raises OlostepSearchError: on API failure
        """
        resolved_key = self.api_key.resolve_value()
        if not resolved_key:
            msg = "OLOSTEP_API_KEY is not set. Set it in your environment or pass it explicitly."
            raise OlostepSearchError(msg)

        try:
            response = requests.post(
                "https://api.olostep.com/v1/searches",
                headers={
                    "Authorization": f"Bearer {resolved_key}",
                    "Content-Type": "application/json",
                },
                json={"query": query, **self.search_params},
                timeout=30,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            msg = f"Olostep /searches request failed: {e.response.status_code} {e.response.text}"
            raise OlostepSearchError(msg) from e
        except requests.RequestException as e:
            msg = f"Olostep /searches network error: {e}"
            raise OlostepSearchError(msg) from e

        data = response.json()
        links_data = data.get("result", {}).get("links", [])

        if self.allowed_domains:
            links_data = [
                link for link in links_data if any(domain in link.get("url", "") for domain in self.allowed_domains)
            ]

        links_data = links_data[: self.top_k]

        documents = [
            Document(
                content=link.get("description", ""),
                meta={
                    "title": link.get("title", ""),
                    "link": link.get("url", ""),
                },
            )
            for link in links_data
        ]
        links = [link.get("url", "") for link in links_data]

        return {"documents": documents, "links": links}

    def to_dict(self) -> dict[str, Any]:
        """Serialize the component to a dictionary."""
        return default_to_dict(
            self,
            api_key=self.api_key.to_dict(),
            top_k=self.top_k,
            allowed_domains=self.allowed_domains,
            search_params=self.search_params,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OlostepWebSearch":
        """Deserialize a component from a dictionary."""
        deserialize_secrets_inplace(data["init_parameters"], keys=["api_key"])
        return default_from_dict(cls, data)
