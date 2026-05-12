---
title: "Olostep"
id: integrations-olostep
description: "Olostep integration for Haystack"
slug: "/integrations-olostep"
---


## olostep_haystack.fetcher

### OlostepFetcherError

Bases: <code>Exception</code>

Raised when Olostep fetching fails.

### OlostepFetcher

Fetch and convert web pages to Markdown using Olostep's scrape API.

Uses SyncOlostepClient (the current Olostep Python SDK).
Do NOT use the legacy Olostep class with client.scrapes.create().

Usage:
from olostep_haystack import OlostepFetcher
fetcher = OlostepFetcher(api_key=Secret.from_env_var("OLOSTEP_API_KEY"))
result = fetcher.run(urls=["https://example.com"])
\# result["documents"] -> List[Document]

#### run

```python
run(urls: list[str]) -> dict[str, Any]
```

Fetch one or more URLs and return their content as Documents.

**Parameters:**

- **urls** (<code>list\[str\]</code>) – list of URLs to scrape

**Returns:**

- <code>dict\[str, Any\]</code> – dict with 'documents' (List[Document])

**Raises:**

- <code>OlostepFetcherError</code> – on API failure

#### to_dict

```python
to_dict() -> dict[str, Any]
```

Serialize the component to a dictionary.

#### from_dict

```python
from_dict(data: dict[str, Any]) -> OlostepFetcher
```

Deserialize a component from a dictionary.

## olostep_haystack.web_search

### OlostepSearchError

Bases: <code>Exception</code>

Raised when Olostep search fails.

### OlostepWebSearch

Search the web using Olostep's /searches endpoint.

Usage:
from olostep_haystack import OlostepWebSearch
search = OlostepWebSearch(api_key=Secret.from_env_var("OLOSTEP_API_KEY"))
result = search.run(query="what is haystack?")
\# result["documents"] -> List[Document]
\# result["links"] -> List[str]

#### run

```python
run(query: str) -> dict[str, Any]
```

Search the web using Olostep.

**Parameters:**

- **query** (<code>str</code>) – the search query string

**Returns:**

- <code>dict\[str, Any\]</code> – dict with 'documents' (List[Document]) and 'links' (List[str])

**Raises:**

- <code>OlostepSearchError</code> – on API failure

#### to_dict

```python
to_dict() -> dict[str, Any]
```

Serialize the component to a dictionary.

#### from_dict

```python
from_dict(data: dict[str, Any]) -> OlostepWebSearch
```

Deserialize a component from a dictionary.
