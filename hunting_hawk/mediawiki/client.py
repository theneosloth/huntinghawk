"""A wrapper for basic Mediawiki API features"""
from dataclasses import dataclass, field
from typing import Any

import requests
import requests_cache

from .__version__ import VERSION


@dataclass(eq=True, frozen=True)
class Client:
    domain: str
    base_path: str
    headers: dict[str, str] = field(
        default_factory=lambda: {
            "User-Agent": f"cargo-export/{VERSION}. https://github.com/theneosloth/cargo"
        },
        kw_only=True,
    )
    timeout: int = field(default=10, kw_only=True)

    def index_endpoint(self) -> str:
        """Construct a mediawiki API endpoint for a given mediawiki site."""
        return f"{self.domain}{self.base_path}"


class ClientError(Exception):
    """Base class for cargo thrown exceptions."""

    pass


class ClientNetworkError(ClientError):
    """Exception class for cargo exceptions related to network failures."""


class ClientDecodeError(ClientError):
    """Exception class for cargo exceptions related to decoding failures."""


class ClientApiError(ClientError):
    """Exception class for cargo exceptions related to API failures."""


def raw_cached_get(
    client: Client, path: str, params: dict[str, Any]
) -> requests.Response:
    """Call a given URL. Caches the response"""
    req_params = params
    req = requests.Request("GET", path, headers=client.headers, params=req_params)
    prepped = req.prepare()

    s = requests_cache.CachedSession(use_temp=True)
    url = prepped.url

    if url is None:
        raise ClientError("Failed to construct url.")
    try:
        request = s.send(prepped, timeout=client.timeout)
        request.raise_for_status()
        return request
    except requests.exceptions.HTTPError as e:
        raise ClientNetworkError from e


def cached_get(
    client: Client, path: str, params: dict[str, Any]
) -> list[str] | dict[Any, Any]:
    """Call a given URL. Caches the response"""
    try:
        res = raw_cached_get(client, path, params).json()
    except requests.exceptions.JSONDecodeError as e:
        raise ClientDecodeError from e

    match res:
        case {"error": err}:
            raise ClientApiError(err)
        case list() | dict():
            return res
        case _:
            raise TypeError("Unknown return type")