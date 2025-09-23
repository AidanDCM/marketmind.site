# Shared Utilities

This package contains shared code used across multiple components of the MarketMind system.

## SP-API Integration

The `shared` package provides a high-level interface to Amazon's Selling Partner API (SP-API) with the following key components:

### Core Components

- `SpapiClient`: Low-level client for making requests to the SP-API
- `SpapiError`: Exception class for SP-API related errors

### Helper Functions

- `get_competitive_pricing()`: Get competitive pricing for one or more ASINs
- `get_buy_box_price()`: Get the current buy box price for an ASIN
- `get_product_details()`: Get detailed product information including pricing
- `get_orders()`: Fetch orders from Amazon SP-API

### Data Models

- `ProductPrice`: Typed dictionary for product price information

## Usage

```python
from marketmind.shared import (
    SpapiClient,
    get_competitive_pricing,
    get_buy_box_price,
    get_product_details,
    get_orders,
    ProductPrice
)

# Initialize the client
client = SpapiClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    refresh_token="your_refresh_token",
    region="na"
)

# Get competitive pricing for an ASIN
pricing = get_competitive_pricing(["B07K3SS94V"])

# Get the buy box price for an ASIN
buy_box_price = get_buy_box_price("B07K3SS94V")

# Get detailed product information
product = get_product_details("B07K3SS94V")

# Fetch recent orders
from datetime import datetime, timedelta
yesterday = datetime.utcnow() - timedelta(days=1)
orders = get_orders(created_after=yesterday)
```

## Configuration

The SP-API client can be configured using environment variables:

- `AMAZON_SP_CLIENT_ID`: Your SP-API client ID
- `AMAZON_SP_CLIENT_SECRET`: Your SP-API client secret
- `AMAZON_SP_REFRESH_TOKEN`: Your SP-API refresh token
- `AMAZON_SP_REGION`: Amazon region (default: 'na')
- `AMAZON_SP_MARKETPLACE_ID`: Amazon Marketplace ID (optional)

## Error Handling

All SP-API functions raise `SpapiError` when an error occurs. Be sure to handle these exceptions in your code.

## Testing

Unit tests for the SP-API integration can be found in the `tests/` directory.
