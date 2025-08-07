import os
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

try:
    from tavily import TavilyClient  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    TavilyClient = None  # type: ignore


class _TTLCache:
    """Very small in-memory TTL cache to reduce duplicate web calls."""

    def __init__(self, ttl_seconds: int = 1200):
        self.ttl_seconds = ttl_seconds
        self._store: Dict[str, Any] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any):
        self._store[key] = (time.time() + self.ttl_seconds, value)


class WebSearchClient:
    """Simple wrapper over a search provider (default: Tavily).

    Normalizes results to a common schema:
      { ref_type: 'web', url, domain, title, snippet, published_at?, score? }
    """

    def __init__(
        self,
        provider: str = None,
        api_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        cache_ttl_s: int = 1200,
    ) -> None:
        self.provider = (provider or os.getenv("SEARCH_PROVIDER") or "tavily").lower()
        self.enabled = (
            enabled if enabled is not None else os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
        )
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._cache = _TTLCache(ttl_seconds=cache_ttl_s)

        self._tavily: Optional[Any] = None
        if self.provider == "tavily" and self.enabled and self.api_key and TavilyClient is not None:
            try:
                self._tavily = TavilyClient(api_key=self.api_key)
            except Exception:
                # Fail soft; we will behave as disabled if client fails
                self._tavily = None

    @staticmethod
    def _extract_domain(url: str) -> str:
        try:
            return urlparse(url).netloc or ""
        except Exception:
            return ""

    def _normalize_results(self, raw_results: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for item in raw_results[: limit or len(raw_results)]:
            url = item.get("url") or item.get("link") or ""
            normalized.append(
                {
                    "ref_type": "web",
                    "url": url,
                    "domain": self._extract_domain(url),
                    "title": item.get("title") or item.get("name") or "",
                    "snippet": item.get("content") or item.get("snippet") or item.get("description") or "",
                    "published_at": item.get("published_date") or item.get("date") or None,
                    "score": item.get("score"),
                }
            )
        return normalized

    def search_snippets(self, query: str, k: int = 5, timeout_s: int = 8) -> List[Dict[str, Any]]:
        """Search the web and return normalized snippet results.

        Returns empty list if disabled or provider/key missing.
        """
        if not self.enabled:
            return []

        cache_key = f"q:{query}|k:{k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        results: List[Dict[str, Any]] = []

        if self.provider == "tavily":
            if not self._tavily:
                return []
            try:
                # tavily-python handles timeouts internally via httpx; keep k modest
                resp = self._tavily.search(
                    query=query,
                    max_results=min(max(k, 1), 10),
                    search_depth="basic",
                    include_answer=False,
                    include_images=False,
                )
                raw_items = resp.get("results", []) if isinstance(resp, dict) else []
                results = self._normalize_results(raw_items, limit=k)
            except Exception:
                results = []
        else:
            # Unsupported provider for now
            results = []

        self._cache.set(cache_key, results)
        return results

    def search_batch(self, queries: List[str], k_each: int = 3) -> List[Dict[str, Any]]:
        all_items: List[Dict[str, Any]] = []
        seen_urls = set()
        for q in queries:
            for item in self.search_snippets(q, k=k_each):
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_items.append(item)
        return all_items


