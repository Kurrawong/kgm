"""Concise errors for inaccessible SPARQL endpoints."""

import re
from contextlib import contextmanager

import httpx2


class SPARQLEndpointError(RuntimeError):
    """The target SPARQL endpoint could not be accessed."""


@contextmanager
def endpoint_errors(endpoint: str):
    url = httpx2.URL(endpoint)
    display_url = url.copy_with(username=None, password=None, query=None, fragment=None)

    def inaccessible(reason):
        return SPARQLEndpointError(
            f"SPARQL Endpoint not accessible: {display_url} ({reason})"
        )

    try:
        yield
    except httpx2.RequestError as error:
        request_url = error.request.url
        if (request_url.scheme, request_url.host, request_url.port) != (
            url.scheme,
            url.host,
            url.port,
        ):
            raise
        reason = (
            "request timed out"
            if isinstance(error, httpx2.TimeoutException)
            else "connection failed"
        )
        raise inaccessible(reason) from error
    except RuntimeError as error:
        # Kurra reports unsuccessful SPARQL HTTP responses in this form.
        status = re.match(r"^ERROR (\d{3}):", str(error))
        if status is None or int(status[1]) not in {
            401,
            403,
            404,
            410,
            *range(500, 600),
        }:
            raise
        raise inaccessible(f"HTTP {status[1]}") from error
