"""Order intake and processing state machine for MarketMind.

This module defines the state machine for processing orders through their lifecycle,
from initial creation to fulfillment and completion.
"""

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from packages.database.models import FulfillmentStatus, Order, OrderItem, OrderStatus, PaymentStatus

from .tax import get_tax_calculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderAction(str, Enum):
    """Actions that can be performed on an order."""

    CREATE = "create"
    VALIDATE = "validate"
    PROCESS_PAYMENT = "process_payment"
    HOLD_FOR_REVIEW = "hold_for_review"
    APPROVE = "approve"
    REJECT = "reject"
    FULFILL = "fulfill"
    SHIP = "ship"
    DELIVER = "deliver"
    CANCEL = "cancel"
    REFUND = "refund"
    ARCHIVE = "archive"


class OrderState(str, Enum):
    """Possible states of an order."""

    DRAFT = "draft"  # Initial state, order is being created
    PENDING = "pending"  # Order is submitted but not yet processed
    PAYMENT_PENDING = "payment_pending"  # Waiting for payment
    PAYMENT_RECEIVED = "payment_received"  # Payment received, processing order
    PAYMENT_FAILED = "payment_failed"  # Payment processing failed
    ON_HOLD = "on_hold"  # Order is on hold for review
    REJECTED = "rejected"  # Order was rejected
    PROCESSING = "processing"  # Order is being processed
    READY_FOR_FULFILLMENT = "ready_for_fulfillment"  # Ready to be fulfilled
    FULFILLED = "fulfilled"  # Order has been fulfilled
    SHIPPED = "shipped"  # Order has been shipped
    DELIVERED = "delivered"  # Order has been delivered
    CANCELLED = "cancelled"  # Order was cancelled
    REFUNDED = "refunded"  # Order was refunded
    ARCHIVED = "archived"  # Order has been archived


class OrderTransition(BaseModel):
    """Represents a state transition for an order."""

    from_state: OrderState
    to_state: OrderState
    action: OrderAction
    requires_human_review: bool = False
    allowed_roles: List[str] = Field(default_factory=lambda: ["admin", "system"])

    def can_transition(self, user_roles: List[str]) -> bool:
        """Check if a user with the given roles can perform this transition."""
        return any(role in self.allowed_roles for role in user_roles)


class OrderStateMachine:
    """State machine for managing order state transitions."""

    # Define valid state transitions
    TRANSITIONS = [
        # Initial creation and validation
        OrderTransition(
            from_state=OrderState.DRAFT,
            to_state=OrderState.PENDING,
            action=OrderAction.VALIDATE,
            requires_human_review=False,
            allowed_roles=["system", "admin", "customer"],
        ),
        OrderTransition(
            from_state=OrderState.PENDING,
            to_state=OrderState.PAYMENT_PENDING,
            action=OrderAction.PROCESS_PAYMENT,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
        # Payment processing
        OrderTransition(
            from_state=OrderState.PAYMENT_PENDING,
            to_state=OrderState.PAYMENT_RECEIVED,
            action=OrderAction.PROCESS_PAYMENT,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
        OrderTransition(
            from_state=OrderState.PAYMENT_PENDING,
            to_state=OrderState.PAYMENT_FAILED,
            action=OrderAction.PROCESS_PAYMENT,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
        # Review and approval
        OrderTransition(
            from_state=OrderState.PAYMENT_RECEIVED,
            to_state=OrderState.ON_HOLD,
            action=OrderAction.HOLD_FOR_REVIEW,
            requires_human_review=True,
            allowed_roles=["system", "admin"],
        ),
        OrderTransition(
            from_state=OrderState.ON_HOLD,
            to_state=OrderState.PROCESSING,
            action=OrderAction.APPROVE,
            requires_human_review=True,
            allowed_roles=["admin", "manager"],
        ),
        OrderTransition(
            from_state=OrderState.ON_HOLD,
            to_state=OrderState.REJECTED,
            action=OrderAction.REJECT,
            requires_human_review=True,
            allowed_roles=["admin", "manager"],
        ),
        # Fulfillment
        OrderTransition(
            from_state=OrderState.PROCESSING,
            to_state=OrderState.READY_FOR_FULFILLMENT,
            action=OrderAction.FULFILL,
            requires_human_review=False,
            allowed_roles=["system", "admin", "fulfillment"],
        ),
        OrderTransition(
            from_state=OrderState.READY_FOR_FULFILLMENT,
            to_state=OrderState.FULFILLED,
            action=OrderAction.FULFILL,
            requires_human_review=False,
            allowed_roles=["system", "admin", "fulfillment"],
        ),
        # Shipping
        OrderTransition(
            from_state=OrderState.FULFILLED,
            to_state=OrderState.SHIPPED,
            action=OrderAction.SHIP,
            requires_human_review=False,
            allowed_roles=["system", "admin", "shipping"],
        ),
        OrderTransition(
            from_state=OrderState.SHIPPED,
            to_state=OrderState.DELIVERED,
            action=OrderAction.DELIVER,
            requires_human_review=False,
            allowed_roles=["system", "admin", "shipping"],
        ),
        # Cancellation and refunds
        OrderTransition(
            from_state=OrderState.PAYMENT_RECEIVED,
            to_state=OrderState.CANCELLED,
            action=OrderAction.CANCEL,
            requires_human_review=True,
            allowed_roles=["admin", "customer_service"],
        ),
        OrderTransition(
            from_state=OrderState.PROCESSING,
            to_state=OrderState.REFUNDED,
            action=OrderAction.REFUND,
            requires_human_review=True,
            allowed_roles=["admin", "finance"],
        ),
        # Archiving
        OrderTransition(
            from_state=OrderState.DELIVERED,
            to_state=OrderState.ARCHIVED,
            action=OrderAction.ARCHIVE,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
        OrderTransition(
            from_state=OrderState.CANCELLED,
            to_state=OrderState.ARCHIVED,
            action=OrderAction.ARCHIVE,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
        OrderTransition(
            from_state=OrderState.REJECTED,
            to_state=OrderState.ARCHIVED,
            action=OrderAction.ARCHIVE,
            requires_human_review=False,
            allowed_roles=["system", "admin"],
        ),
    ]

    @classmethod
    def get_valid_transitions(
        cls, current_state: Union[OrderState, str], user_roles: Optional[List[str]] = None
    ) -> List[OrderTransition]:
        """Get all valid transitions from the current state.

        Args:
            current_state: The current order state
            user_roles: Roles of the user requesting the transition

        Returns:
            List of valid OrderTransition objects
        """
        if isinstance(current_state, str):
            current_state = OrderState(current_state)

        if user_roles is None:
            user_roles = ["system"]

        return [
            t
            for t in cls.TRANSITIONS
            if t.from_state == current_state and t.can_transition(user_roles)
        ]

    @classmethod
    def can_transition(
        cls,
        current_state: Union[OrderState, str],
        target_state: Union[OrderState, str],
        user_roles: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Check if a transition is valid.

        Args:
            current_state: Current order state
            target_state: Desired target state
            user_roles: Roles of the user requesting the transition

        Returns:
            Tuple of (is_valid, error_message)
        """
        if isinstance(current_state, str):
            current_state = OrderState(current_state)
        if isinstance(target_state, str):
            target_state = OrderState(target_state)

        if user_roles is None:
            user_roles = ["system"]

        valid_transitions = cls.get_valid_transitions(current_state, user_roles)

        for transition in valid_transitions:
            if transition.to_state == target_state:
                return True, None

        return (
            False,
            f"Invalid transition from {current_state} to {target_state} for roles {user_roles}",
        )


class OrderIntake:
    """Handles the order intake and processing workflow."""

    def __init__(self, db: Session):
        """Initialize with a database session."""
        self.db = db
        self.tax_calculator = get_tax_calculator()

    def create_order(self, order_data: Dict[str, Any], user_id: int) -> Order:
        """Create a new order.

        Args:
            order_data: Dictionary containing order data
            user_id: ID of the user creating the order

        Returns:
            The created Order object
        """
        # Idempotency: compute a deterministic key using order_number + channel + subtotal
        order_number = order_data.get("order_number")
        channel = order_data.get("channel") or order_data.get("source") or "unknown"
        idempotency_basis = f"{order_number}|{channel}|{order_data.get('subtotal')}".encode("utf-8")
        try:
            import hashlib

            idem_key = hashlib.sha256(idempotency_basis).hexdigest()[:32]
        except Exception:
            idem_key = f"fallback-{order_number}-{channel}"

        # If an order with the same order_number and idempotency_key exists, return it
        if order_number:
            existing = self.db.query(Order).filter(Order.order_number == order_number).first()
            if existing and isinstance(getattr(existing, "meta", None), dict):
                if existing.meta.get("idempotency_key") == idem_key:
                    logger.info(
                        f"Idempotent create: existing order {existing.id} for order_number={order_number}"
                    )
                    return existing

        # Calculate taxes
        tax_result = self._calculate_taxes(order_data)

        # Create order items (align with DB model fields)
        order_items = []
        for item_data in order_data.get("items", []):
            order_item = OrderItem(
                product_id=item_data.get("product_id"),
                sku=item_data.get("sku"),
                product_name=item_data.get("name"),
                quantity=int(item_data["quantity"]),
                price=Decimal(str(item_data.get("unit_price", item_data.get("price")))),
                tax_amount=Decimal(str(item_data.get("tax_amount", 0))),
                discount_amount=Decimal(str(item_data.get("discount_amount", 0))),
            )
            order_items.append(order_item)

        # Create the order (align with DB model fields)
        # Attach idempotency key to meta
        meta = order_data.get("metadata", {}) or {}
        if isinstance(meta, dict):
            meta.setdefault("idempotency_key", idem_key)

        order = Order(
            customer_id=user_id,
            order_number=order_data.get("order_number"),
            status=OrderStatus.DRAFT,
            payment_status=PaymentStatus.PENDING,
            fulfillment_status=FulfillmentStatus.UNFULFILLED,
            subtotal=Decimal(str(order_data["subtotal"])),
            total_tax=Decimal(str(tax_result["total_tax"])),
            total_shipping=Decimal(
                str(order_data.get("shipping_amount", order_data.get("total_shipping", 0)))
            ),
            total_discounts=Decimal(
                str(order_data.get("discount_amount", order_data.get("total_discounts", 0)))
            ),
            currency=order_data.get("currency", "USD"),
            meta=meta,
            items=order_items,
        )

        # Compute order total from items and adjustments per model helper
        try:
            order.calculate_totals()
        except (AttributeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to calculate order totals, using fallback: {e}")
            # Fallback: ensure total is at least subtotal + shipping + tax - discounts
            order.total = (
                order.subtotal + order.total_shipping + order.total_tax - order.total_discounts
            )
        except Exception as e:
            logger.error(f"Unexpected error calculating order totals: {e}", exc_info=True)
            # Fallback: ensure total is at least subtotal + shipping + tax - discounts
            order.total = (
                order.subtotal + order.total_shipping + order.total_tax - order.total_discounts
            )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        logger.info(f"Created order {order.id} in DRAFT state with {len(order_items)} items")
        return order

    def process_order(
        self,
        order_id: int,
        user_roles: Optional[List[str]] = None,
        expected_updated_at: Optional[datetime] = None,
    ) -> Order:
        """Process an order through its state machine.

        Args:
            order_id: ID of the order to process
            user_roles: Roles of the user performing the action

        Returns:
            The updated Order object
        """
        if user_roles is None:
            user_roles = ["system"]

        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Optimistic concurrency guard
        if expected_updated_at is not None and order.updated_at != expected_updated_at:
            raise ValueError(
                f"Order {order_id} update conflict: expected_updated_at={expected_updated_at.isoformat()} actual={order.updated_at.isoformat()}"
            )

        current_state = OrderState(order.status)

        # Determine the next state based on current state
        if current_state == OrderState.DRAFT:
            # Move from DRAFT to PENDING (requires validation)
            self._validate_order(order)
            next_state = OrderState.PENDING
            action = OrderAction.VALIDATE
        elif current_state == OrderState.PENDING:
            # Move from PENDING to PAYMENT_PENDING (start payment processing)
            next_state = OrderState.PAYMENT_PENDING
            action = OrderAction.PROCESS_PAYMENT
        elif current_state == OrderState.PAYMENT_PENDING:
            # Process payment (in a real app, this would call a payment processor)
            payment_successful = self._process_payment(order)
            next_state = (
                OrderState.PAYMENT_RECEIVED if payment_successful else OrderState.PAYMENT_FAILED
            )
            action = OrderAction.PROCESS_PAYMENT
        elif current_state == OrderState.PAYMENT_RECEIVED:
            # Check if order needs review
            if self._needs_review(order):
                next_state = OrderState.ON_HOLD
                action = OrderAction.HOLD_FOR_REVIEW
            else:
                next_state = OrderState.PROCESSING
                action = OrderAction.APPROVE
        else:
            # For other states, we don't automatically transition
            logger.info(f"No automatic transition from state {current_state}")
            return order

        # Validate the transition
        is_valid, error_message = OrderStateMachine.can_transition(
            current_state, next_state, user_roles
        )

        if not is_valid:
            logger.error(f"Invalid transition: {error_message}")
            raise ValueError(error_message)

        # Update the order state
        prev_updated_at = order.updated_at
        order.status = next_state
        order.updated_at = datetime.now(timezone.utc)

        # Log the state transition
        self._log_state_change(order, current_state, next_state, action, user_roles)

        # Append lightweight audit annotation into order.meta
        try:
            audit_entry = {
                "ts": order.updated_at.isoformat(),
                "from": current_state.value,
                "to": next_state.value,
                "action": action.value,
                "roles": user_roles,
                "prev_updated_at": prev_updated_at.isoformat() if prev_updated_at else None,
            }
            if not isinstance(order.meta, dict):
                order.meta = {}
            audit_list = order.meta.get("audit")
            if not isinstance(audit_list, list):
                audit_list = []
            audit_list.append(audit_entry)
            order.meta["audit"] = audit_list
        except Exception:
            # Non-fatal; audit persistence can be handled elsewhere
            logger.debug("Failed to append audit entry to order.meta", exc_info=True)

        self.db.commit()
        self.db.refresh(order)

        logger.info(f"Order {order.id} transitioned from {current_state} to {next_state}")
        return order

    def _calculate_taxes(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate taxes for an order.

        Args:
            order_data: Order data including items and addresses

        Returns:
            Dictionary with total tax and breakdown
        """
        shipping_address = order_data.get("shipping_address", {})

        # Phase 8: choose tax model and provider seam
        tax_model = (
            "marketplace_collected"
            if order_data.get("marketplace_collected")
            else order_data.get("tax_model", "seller_collected")
        )
        provider = os.getenv("TAX_PROVIDER", "none").lower() or "none"

        buyer_region = {
            "country": shipping_address.get("country"),
            "state": shipping_address.get("state"),
            "postal_code": shipping_address.get("postal_code"),
        }

        subtotal = Decimal(str(order_data["subtotal"]))
        shipping_cost = Decimal(str(order_data.get("shipping_amount", 0)))

        if hasattr(self.tax_calculator, "calculate_with_model"):
            return self.tax_calculator.calculate_with_model(
                tax_model=tax_model,  # marketplace_collected | seller_collected
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                buyer_region=buyer_region,
                channel_reported_tax=(
                    Decimal(str(order_data.get("channel_reported_tax", 0)))
                    if order_data.get("channel_reported_tax") is not None
                    else None
                ),
                provider=provider,  # none|taxjar|avalara
                provider_ctx=None,
            )

        # Fallback to legacy single-path calculator
        return self.tax_calculator.calculate_tax(
            subtotal=subtotal,
            country_code=buyer_region["country"],
            state_code=buyer_region["state"],
            postal_code=buyer_region["postal_code"],
            shipping_cost=shipping_cost,
        )

    def _validate_order(self, order: Order) -> bool:
        """Validate an order.

        Args:
            order: The order to validate

        Returns:
            bool: True if order is valid, False otherwise
        """
        # In a real app, this would perform validation like:
        # - Check product availability
        # - Validate shipping address
        # - Check for fraud indicators
        # - Apply any promotions or discounts

        # For now, just log the validation
        logger.info(f"Validating order {order.id}")
        return True

    def _process_payment(self, order: Order) -> bool:
        """Process payment for an order.

        Args:
            order: The order to process payment for

        Returns:
            bool: True if payment was successful, False otherwise
        """
        # In a real app, this would integrate with a payment processor
        # like Stripe, PayPal, etc.

        logger.info(f"Processing payment for order {order.id}")

        # Simulate payment processing
        # In a real app, this would make an API call to the payment processor
        # and handle the response
        payment_successful = True  # Simulate successful payment

        if payment_successful:
            order.payment_status = PaymentStatus.PAID
            order.paid_at = datetime.now(timezone.utc)
            logger.info(f"Payment for order {order.id} was successful")
        else:
            order.payment_status = PaymentStatus.FAILED
            logger.warning(f"Payment for order {order.id} failed")

        self.db.commit()
        return payment_successful

    def _needs_review(self, order: Order) -> bool:
        """Determine if an order needs manual review.

        Args:
            order: The order to check

        Returns:
            bool: True if the order needs review, False otherwise
        """
        # In a real app, this would check things like:
        # - High order amount
        # - High-risk shipping address
        # - Suspicious activity
        # - Manual review flags

        # For now, just return False (no review needed)
        return False

    def _log_state_change(
        self,
        order: Order,
        from_state: OrderState,
        to_state: OrderState,
        action: OrderAction,
        user_roles: List[str],
        notes: Optional[str] = None,
    ) -> None:
        """Log a state change for an order.

        Args:
            order: The order being updated
            from_state: Previous state
            to_state: New state
            action: Action that caused the state change
            user_roles: Roles of the user who performed the action
            notes: Optional notes about the state change
        """
        # In a real app, this would log to a dedicated audit table
        logger.info(
            f"Order {order.id} state changed from {from_state} to {to_state} "
            f"via {action} by {user_roles}. Notes: {notes or 'N/A'}"
        )
