#!/usr/bin/env python3
"""
eBay Integration Test Script

This script tests the eBay integration by performing the following actions:
1. Testing authentication
2. Testing product operations
   - Create product
   - Get product
   - Update product
   - Update inventory
   - Delete product
3. Testing order operations
   - Get orders
   - Get order by ID
   - Update order status
4. Testing error handling and edge cases
5. Cleaning up test data
"""

import os
import sys
import time
import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from config.ebay_config import get_ebay_config
from packages.connectors.channels.ebay import EBayAdapter, OrderStatus
from packages.connectors.shared.exceptions import ChannelDataError

# Load environment variables from .env file
load_dotenv()


class EBayIntegrationTest(unittest.TestCase):
    """Test class for eBay integration."""

    # Class-level configuration
    config: Dict[str, Any] = {}
    adapter: Optional[EBayAdapter] = None
    test_product_id = None
    test_order_id = None
    test_sku = f"TEST_{int(time.time())}"

    @classmethod
    def setUpClass(cls):
        """Set up test class with configuration."""
        # Initialize configuration
        cls.config = get_ebay_config()
        cls.config["sandbox"] = True  # Always use sandbox for tests

    def setUp(self):
        """Set up test case."""
        if not self.adapter:
            self.adapter = EBayAdapter(self.config)
            if not self.adapter.authenticate():
                self.fail("Failed to authenticate with eBay API")

    def test_authentication(self):
        """Test authentication with eBay API."""
        print("\n1. Testing Authentication...")

        # Test authentication
        self.assertTrue(self.adapter.authenticate(), "Authentication failed")
        print(
            f"  ✓ Authenticated successfully (Token expires at: {self.adapter.config.token_expiry})"
        )

        # Test token refresh
        old_token = self.adapter.config.auth_token
        self.assertTrue(self.adapter.authenticate(force_refresh=True), "Token refresh failed")
        self.assertNotEqual(old_token, self.adapter.config.auth_token, "Token was not refreshed")
        print("  ✓ Token refresh successful")

    def test_product_operations(self):
        """Test product CRUD operations."""
        print("\n2. Testing Product Operations...")

        # Test create product
        print("  Testing product creation...")
        try:
            test_product = self.adapter.create_product(
                {
                    "title": "Test Product",
                    "description": "A test product",
                    "price": 9.99,
                    "quantity": 10,
                    "sku": self.test_sku,
                }
            )
            self.test_product_id = test_product.item_id
            print(f"  ✓ Created test product: {self.test_sku} (ID: {self.test_product_id})")
        except Exception as e:
            self.fail(f"Failed to create test product: {e}")

        # Test get product
        print("  Testing product retrieval...")
        try:
            product = self.adapter.get_product(self.test_product_id)
            self.assertIsNotNone(product, "Product not found")
            print(
                f"  ✓ Retrieved test product: {product.title} (SKU: {product.sku}, Qty: {getattr(product, 'quantity', 'N/A')})"
            )
        except Exception as e:
            self.fail(f"Failed to get test product: {e}")

        # Test update inventory
        print("  Testing inventory update...")
        try:
            updates = [{"sku": self.test_sku, "quantity": 5}]
            print(f"  - Updating inventory for SKU {self.test_sku} to quantity 5")
            success = self.adapter.update_inventory(updates)
            self.assertTrue(success, "Inventory update failed")

            # Verify inventory was updated
            print(f"  - Fetching updated product with ID: {self.test_product_id}")
            updated_product = self.adapter.get_product(self.test_product_id)
            print(
                f"  - Retrieved updated product: SKU={updated_product.sku}, Qty={getattr(updated_product, 'quantity', 'N/A')}"
            )

            if not hasattr(updated_product, "quantity"):
                self.fail("Product does not have a quantity attribute")

            self.assertEqual(
                updated_product.quantity,
                5,
                f"Inventory quantity not updated. Expected 5, got {updated_product.quantity}",
            )

            print("  ✓ Inventory updated and verified successfully")
        except Exception as e:
            print(f"  ✗ Error during inventory update test: {str(e)}")
            import traceback

            traceback.print_exc()
            self.fail(f"Failed to update inventory: {e}")

        return True

    def test_order_operations(self):
        """Test order operations."""
        print("\n3. Testing Order Operations...")

        # Test get orders
        print("  Testing order retrieval...")
        try:
            # Get recent orders
            orders = self.adapter.get_orders(
                status=OrderStatus.ACTIVE,
                start_date=datetime.utcnow() - timedelta(days=30),
                limit=5,
            )
            self.assertIsInstance(orders, list, "Expected a list of orders")

            if orders:
                self.test_order_id = orders[0].order_id
                print(f"  ✓ Retrieved {len(orders)} recent orders")

                # Test get single order
                print("  Testing single order retrieval...")
                order = self.adapter.get_order(self.test_order_id)
                self.assertIsNotNone(order, "Failed to retrieve order by ID")
                print(f"  ✓ Retrieved order: {order.order_id}")
            else:
                print("  ⚠ No orders found to test with")

        except Exception as e:
            self.fail(f"Order operation failed: {e}")

        return True

    def test_error_handling(self):
        """Test error handling and edge cases."""
        print("\n4. Testing Error Handling...")

        # Test invalid product ID
        print("  Testing invalid product ID...")
        with self.assertRaises(ChannelDataError):
            self.adapter.get_product("INVALID_PRODUCT_ID_123")
        print("  ✓ Handled invalid product ID")

        # Test invalid order ID
        print("  Testing invalid order ID...")
        with self.assertRaises(ChannelDataError):
            self.adapter.get_order("INVALID_ORDER_ID_123")
        print("  ✓ Handled invalid order ID")

        # Test empty inventory update
        print("  Testing empty inventory update...")
        try:
            success = self.adapter.update_inventory([])
            self.assertTrue(success, "Empty inventory update should succeed")
            print("  ✓ Handled empty inventory update")
        except Exception as e:
            self.fail(f"Empty inventory update failed: {e}")

        return True

    @classmethod
    def tearDownClass(cls):
        """Clean up test data."""
        print("\nCleaning up test data...")

        if not cls.adapter:
            return

        # Clean up test product
        if cls.test_sku:
            try:
                cls.adapter.delete_product(cls.test_sku)
                print(f"  - Deleted test product: {cls.test_sku}")
            except Exception as e:
                print(f"  - Error cleaning up test product: {e}")

        # Clean up test orders (if any were created)
        try:
            # This would be implemented to clean up any test orders
            print("  - Test order cleanup would be implemented here")
        except Exception as e:
            print(f"  - Error cleaning up test orders: {e}")


def main():
    """Main function to run the tests."""
    # Initialize test class to set up configuration
    test_class = EBayIntegrationTest()
    test_class.setUpClass()

    # Configure test runner
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(EBayIntegrationTest)

    # Run tests
    print("=" * 80)
    print(
        f"eBay {'Sandbox' if test_class.config.get('sandbox', True) else 'Production'} Integration Tests"
    )
    print("=" * 80)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Clean up after tests
    test_class.tearDownClass()

    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
