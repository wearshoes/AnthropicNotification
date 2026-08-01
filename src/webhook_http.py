"""Bounded webhook HTTP delivery with business-response validation."""

from __future__ import annotations

import time

import requests


DEFAULT_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 10
MIN_DISPLAY_ERRCODE = -(2**31)
MAX_DISPLAY_ERRCODE = 2**31 - 1


class WebhookDeliveryError(RuntimeError):
    """Raised when a webhook cannot confirm business-level success."""


def _is_success_errcode(errcode: object) -> bool:
    return type(errcode) is int and errcode == 0


def _safe_errcode(errcode: object) -> str:
    if (
        type(errcode) is int
        and MIN_DISPLAY_ERRCODE <= errcode <= MAX_DISPLAY_ERRCODE
    ):
        return str(errcode)
    return "unknown"


def _validated_response(response) -> dict:
    response.raise_for_status()
    status = getattr(response, "status_code", None)
    if isinstance(status, int) and not 200 <= status < 300:
        raise WebhookDeliveryError(f"webhook returned HTTP status {status}")

    try:
        data = response.json()
    except (TypeError, ValueError) as exc:
        raise WebhookDeliveryError("webhook returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise WebhookDeliveryError("webhook response was not a JSON object")
    errcode = data.get("errcode")
    if not _is_success_errcode(errcode):
        raise WebhookDeliveryError(
            f"webhook rejected request: errcode={_safe_errcode(errcode)}"
        )
    return data


def post_json(
    webhook_url: str,
    payload: dict,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """POST JSON and retry without exposing the credential-bearing URL."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=timeout,
                allow_redirects=False,
            )
            return _validated_response(response)
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    if isinstance(last_error, WebhookDeliveryError):
        raise last_error
    error_type = type(last_error).__name__ if last_error is not None else "UnknownError"
    raise WebhookDeliveryError(
        f"webhook delivery failed after {attempts} attempt(s): {error_type}"
    ) from last_error
