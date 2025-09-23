"""Fulfillment and tracking publish scaffold.

Provides seams to buy labels (EasyPost/Shippo) or accept supplier tracking, and publish to channels.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Tracking:
    carrier: str
    service: str
    tracking_no: str


class FulfillmentService:
    def __init__(self, easypost_key: Optional[str] = None, shippo_key: Optional[str] = None):
        self.easypost_key = easypost_key
        self.shippo_key = shippo_key

    def buy_label(self, shipment: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: integrate EasyPost/Shippo and return purchased label + cost
        return {
            "label_url": "https://stub/label.pdf",
            "cost_cents": 1099,
            "carrier": "UPS",
            "service": "Ground",
        }

    def publish_tracking(self, channel: str, order_ref: str, tracking: Tracking) -> bool:
        # TODO: integrate per-channel publish (Amazon/eBay/Shopify adapters)
        return True
