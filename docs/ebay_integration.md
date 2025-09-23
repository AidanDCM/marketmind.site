# eBay Integration

This document provides comprehensive information on how to integrate with the eBay Marketplace API using MarketMind's eBay adapter. The integration has been thoroughly tested and includes support for product management, inventory synchronization, and order processing.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Authentication](#authentication)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, you'll need:

1. An eBay Developer Account
   - Sign up at: https://developer.ebay.com/
2. An eBay Application Key (App ID, Cert ID, and Dev ID)
   - Create a new app in the [eBay Developer Portal](https://developer.ebay.com/my/keys)
3. A Redirect URI (RuName)
   - Configure this in your eBay Developer Account under "Account" > "Production" > "User Tokens"
4. Python 3.8 or higher
5. Required Python packages (see Setup section)

## Setup

### 1. Environment Variables

Create a `.env` file in your project root with the following variables:

```ini
# eBay API Credentials
EBAY_APP_ID=Your-App-ID
EBAY_CERT_ID=Your-Cert-ID
EBAY_DEV_ID=Your-Dev-ID
EBAY_RU_NAME=Your-RuName
EBAY_SANDBOX=true  # Set to false for production

# Optional - Will be set during OAuth flow
# EBAY_AUTH_TOKEN=your-auth-token
# EBAY_REFRESH_TOKEN=your-refresh-token
```

### 2. Install Dependencies

Make sure you have the required Python packages installed:

```bash
pip install -r infra/docker/requirements-api.txt
pip install -r infra/docker/requirements-worker.txt
```

## Authentication

eBay uses OAuth 2.0 for authentication. The integration includes a helper script (`scripts/ebay_auth.py`) to simplify the authentication process. The adapter automatically handles token refresh when needed.

The first time you set up the integration, you'll need to authorize the application:

### 1. Get Authorization URL

Run the following command to get the authorization URL:

```bash
python scripts/ebay_auth.py get-auth-url
```

This will open your default web browser to the eBay authorization page. If it doesn't, copy and paste the URL from the console output.

### 2. Authorize the Application

1. Log in to your eBay account when prompted
2. Review the permissions and click "I agree"
3. You'll be redirected to your RuName URL

### 3. Exchange Code for Token

After authorizing, you'll be redirected to your RuName URL with an authorization code. Copy the full URL and run:

```bash
python scripts/ebay_auth.py exchange-code "YOUR_FULL_REDIRECT_URL"
```

This will exchange the authorization code for an access token and refresh token. Add these to your `.env` file.

## Usage

### Initialize the eBay Adapter

```python
from packages.connectors.channels.ebay import EBayAdapter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# For most use cases, initialize with default configuration from environment variables
ebay = EBayAdapter()

# For advanced usage, you can provide a custom configuration and database session
config = {
    "app_id": "your-app-id",
    "cert_id": "your-cert-id",
    "dev_id": "your-dev-id",
    "sandbox": True,  # Set to False for production
    "auth_token": "your-auth-token",
    "refresh_token": "your-refresh-token"
}

# Optional: Set up a database session for order tracking
engine = create_engine('sqlite:///marketmind.db')
Session = sessionmaker(bind=engine)
db_session = Session()

ebay = EBayAdapter(config=config, db_session=db_session)
```

### Get Product Categories

```python
# Get top-level categories
categories = ebay.get_categories()

# Get subcategories for a specific category
subcategories = ebay.get_categories(parent_id="parent-category-id")
```

### List a Product

```python
product_data = {
    "title": "Test Product",
    "description": "This is a test product.",
    "price": 19.99,
    "quantity": 10,
    "condition": "NEW",
    "category_id": "test-category-id",
    "sku": "TEST-001",
    "images": ["https://example.com/image.jpg"],
    "shipping_options": [
        {
            "type": "FLAT",
            "cost": 5.99,
            "priority": 1,
            "service": "USPS_GROUND"
        }
    ]
}

# Create the listing
listing = ebay.create_product(product_data)
print(f"Created listing: {listing['item_id']}")
```

### Get Orders

```python
# Get recent orders
orders = ebay.get_orders()

# Get orders by status
pending_orders = ebay.get_orders(status="PENDING")

# Get orders within a date range
from datetime import datetime, timedelta
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=7)
recent_orders = ebay.get_orders(start_date=start_date, end_date=end_date)
```

### Update Order Status

```python
# Update order status
ebay.update_order_status(
    order_id="order-123",
    status="SHIPPED",
    tracking_number="1Z12345E0205271688",
    carrier="UPS"
)
```

### Update Inventory

Update inventory levels for one or more products. The adapter supports both SKU-based and item ID-based updates.

```python
# Update inventory using SKUs
updates = [
    {'sku': 'ITEM123', 'quantity': 10},
    {'sku': 'ITEM456', 'quantity': 5}
]
success = ebay.update_inventory(updates)

# Verify the update
for item in updates:
    product = ebay.get_product(item['sku'])
    print(f"SKU: {product.sku}, New Quantity: {product.quantity}")
```

## Recent Updates

### v1.1.0 - 2025-08-13
- **Fixed**: Resolved inventory update persistence issues
- **Improved**: Enhanced error handling for product retrieval
- **Added**: Support for both SKU and item ID lookups
- **Fixed**: FieldInfo object handling in product retrieval
- **Improved**: Mock data store for testing

### v1.0.0 - 2025-08-10
- Initial release of eBay integration

## API Reference

### EBayAdapter Class

#### `__init__(self, config: Optional[Dict] = None, db_session: Optional[Session] = None)`

Initialize the eBay adapter.

**Parameters:**
- `config` (Dict, optional): Configuration dictionary. If not provided, loads from environment variables.
- `db_session` (Session, optional): SQLAlchemy database session.

#### `update_inventory(self, updates: List[Dict[str, Any]], **kwargs) -> bool`

Update inventory levels for multiple products on eBay. The method supports both SKU and item ID based updates.

**Parameters:**
- `updates` (List[Dict]): List of inventory updates, where each update is a dictionary
  containing either:
  - 'sku' (str): The product's SKU
  - 'item_id' (str): The eBay item ID
  - 'quantity' (int): The new inventory quantity
- `**kwargs`: Additional keyword arguments for the request.

**Returns:**
- `bool`: True if the update was successful, False otherwise

**Raises:**
- `ChannelConnectionError`: If there's an error connecting to the eBay API
- `ChannelDataError`: If there's an error in the request data

**Example:**
```python
# Update inventory using SKUs
updates = [
    {'sku': 'ITEM123', 'quantity': 10},
    {'item_id': 'v1|123456789012|123456789012', 'quantity': 5}
]
success = ebay.update_inventory(updates)
- `bool`: True if the update was successful, False otherwise.

**Raises:**
- `ChannelConnectionError`: If there's an error connecting to the eBay API.
- `ChannelDataError`: If there's an error in the request data.

**Example:**
```python
updates = [
    {'sku': 'ITEM123', 'quantity': 10},
    {'sku': 'ITEM456', 'quantity': 5}
]
success = ebay.update_inventory(updates)
```

#### `get_orders(self, status: Optional[OrderStatus] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100, offset: int = 0) -> List[EBayOrder]`

Get orders from eBay.

**Parameters:**
- `status` (OrderStatus, optional): Filter by order status.
- `start_date` (datetime, optional): Filter by order creation date (start).
- `end_date` (datetime, optional): Filter by order creation date (end).
- `limit` (int, optional): Maximum number of orders to return. Defaults to 100.
- `offset` (int, optional): Pagination offset. Defaults to 0.

#### `get_order(self, order_id) -> Optional[EBayOrder]`
- List[EBayOrder]: List of orders

#### `get_order(order_id)`
Get a single order by ID.

**Parameters:**
- `order_id` (str): The eBay order ID.

**Returns:**
- Optional[EBayOrder]: The order, or None if not found

#### `create_product(product_data)`
Create a new product listing.

**Parameters:**
- `product_data` (dict): Product data including title, description, price, etc.

**Returns:**
- dict: The created listing data

#### `update_product(product_id, product_data)`
Update an existing product listing.

**Parameters:**
- `product_id` (str): The eBay item ID or SKU.
- `product_data` (dict): Updated product data.

**Returns:**
- dict: The updated listing data

#### `delete_product(product_id)`
Delete a product listing.

**Parameters:**
- `product_id` (str): The eBay item ID or SKU.

**Returns:**
- bool: True if deletion was successful

## Testing

### Running Tests

To run the integration tests:

```bash
# Test against sandbox (default)
python scripts/test_ebay_integration.py

# Test against production
python scripts/test_ebay_integration.py --production
```

### Test Coverage

The test script verifies the following functionality:
1. Authentication
2. Category fetching
3. Product operations (create, update, delete)
4. Order operations (fetch, update status)

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure your API keys are correct and have the necessary permissions
   - Check that your system clock is synchronized (NTP recommended)
   - Verify your RuName is correctly configured in the eBay Developer Portal

2. **Inventory Update Issues**
   - Ensure you're using the correct SKU or item ID
   - Check that the quantity is a positive integer
   - Verify your account has sufficient selling limits

3. **Rate Limiting**
   - The eBay API has rate limits. If you encounter 429 errors, implement exponential backoff in your requests.
   - Consider implementing request queuing for high-volume operations

4. **Sandbox vs Production**
   - Test thoroughly in the sandbox environment before moving to production
   - Note that some operations may behave differently in the sandbox

## Support

For additional support with the eBay integration:

1. **Documentation**
   - [eBay Developer Program](https://developer.ebay.com/)
   - [eBay API Documentation](https://developer.ebay.com/api-docs/static/rest-landing.html)

2. **Community**
   - [eBay Developer Forums](https://forums.developer.ebay.com/)
   - [Stack Overflow](https://stackoverflow.com/questions/tagged/ebay-api)

3. **Support**
   - For issues with the MarketMind eBay adapter, please open an issue on our GitHub repository
   - For eBay API issues, contact [eBay Developer Support](https://developer.ebay.com/support/)

## Conclusion

The MarketMind eBay integration provides a robust solution for managing your eBay store inventory and orders. With support for both SKU and item ID based operations, it offers flexibility for various e-commerce workflows. The adapter handles authentication, error handling, and rate limiting, allowing you to focus on your business logic.

For production deployments, we recommend:
1. Implementing proper error handling and logging
2. Setting up monitoring for API rate limits
3. Regularly testing the integration in the sandbox environment
4. Keeping your API credentials secure
5. Staying updated with eBay's API changes and updates of the MarketMind project. See the main project for licensing information.
