#!/usr/bin/env python3
"""Print masked Stripe/Shopify integration readiness (no secrets)."""

from __future__ import annotations

from marketmind.commerce_integrations import get_commerce_integration_status


def main() -> None:
    status = get_commerce_integration_status()
    print(status)


if __name__ == "__main__":
    main()
