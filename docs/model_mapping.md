# Database Model Mapping

This document outlines how third-party database models are mapped to MarketMind's schema.

## Source: Free Retail Arbitrage Models

### 1. Product Model

**Source Table**: `products`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| name | name | String | Product name |
| price | price | Float | Current selling price |
| stock | quantity | Integer | Available quantity |
| - | sku | String | Add SKU field |
| - | description | Text | Product description |
| - | created_at | DateTime | Creation timestamp |
| - | updated_at | DateTime | Last update timestamp |

### 2. Customer Model

**Source Table**: `customers`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| name | name | String | Customer name |
| email | email | String | Customer email (unique) |
| - | phone | String | Customer phone number |
| - | address | JSONB | Shipping/billing addresses |
| - | created_at | DateTime | Creation timestamp |
| - | updated_at | DateTime | Last update timestamp |

### 3. Order Model

**Source Table**: `orders`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| customer_id | customer_id | Integer | Foreign key to customers |
| total_amount | total_amount | Float | Order total |
| - | order_number | String | Unique order identifier |
| - | status | String | Order status (new, processing, shipped, etc.) |
| - | items | JSONB | Order line items |
| - | shipping_address | JSONB | Shipping information |
| - | billing_address | JSONB | Billing information |
| - | created_at | DateTime | Creation timestamp |
| - | updated_at | DateTime | Last update timestamp |

### 4. Supplier Model

**Source Table**: `suppliers`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| name | name | String | Supplier name |
| contact_info | contact_info | JSONB | Contact information |
| - | email | String | Primary contact email |
| - | phone | String | Primary contact phone |
| - | address | JSONB | Business address |
| - | created_at | DateTime | Creation timestamp |
| - | updated_at | DateTime | Last update timestamp |

### 5. CustomerQuery Model

**Source Table**: `customer_queries`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| customer_id | customer_id | Integer | Foreign key to customers |
| order_id | order_id | Integer | Optional foreign key to orders |
| query_text | content | Text | Query content |
| query_timestamp | created_at | DateTime | When the query was created |
| resolved | is_resolved | Boolean | Whether the query is resolved |
| escalated | is_escalated | Boolean | Whether the query was escalated |
| - | status | String | Query status (open, in_progress, resolved) |
| - | assigned_to | Integer | Foreign key to users |
| - | updated_at | DateTime | Last update timestamp |

### 6. ChatbotInteraction Model

**Source Table**: `chatbot_interactions`

| Source Field | MarketMind Field | Type | Notes |
|--------------|------------------|------|-------|
| id | id | Integer | Primary key |
| query_id | customer_query_id | Integer | Foreign key to customer_queries |
| message | content | Text | Message content |
| is_bot | is_from_bot | Boolean | Whether the message is from the bot |
| timestamp | created_at | DateTime | When the message was sent |
| - | metadata | JSONB | Additional message metadata |

## Migration Strategy

1. **Schema Updates**:
   - Add any missing columns to existing tables
   - Create new tables for models that don't exist
   - Set up appropriate indexes and constraints

2. **Data Migration**:
   - Write scripts to migrate existing data
   - Handle data transformation and cleanup
   - Preserve relationships between entities

3. **Backward Compatibility**:
   - Maintain API compatibility where possible
   - Update any affected queries and business logic
   - Add database views if needed for backward compatibility

## Next Steps

1. Review and finalize the mapping
2. Create Alembic migration scripts
3. Test the migration in a staging environment
4. Schedule and execute the production migration
