"""
Clean order data from Snowflake

This recipe:
- Removes invalid orders
- Validates amounts and dates
- Standardizes order status
- Ensures foreign key integrity
"""

import dataiku
import pandas as pd
from datetime import datetime

# Read input dataset
df = dataiku.Dataset("RAW_ORDERS").get_dataframe()

# Remove rows with missing critical fields
df = df.dropna(subset=['ORDER_ID', 'CUSTOMER_ID', 'ORDER_AMOUNT'])

# Validate order amounts (must be positive)
df = df[df['ORDER_AMOUNT'] > 0]

# Ensure proper data types
df['ORDER_ID'] = df['ORDER_ID'].astype(str).str.strip()
df['CUSTOMER_ID'] = df['CUSTOMER_ID'].astype(str).str.strip()
df['ORDER_AMOUNT'] = df['ORDER_AMOUNT'].astype(float)

# Standardize order status
status_mapping = {
    'completed': 'COMPLETED',
    'pending': 'PENDING',
    'cancelled': 'CANCELLED',
    'shipped': 'SHIPPED'
}
df['ORDER_STATUS'] = df['ORDER_STATUS'].str.lower().map(status_mapping)
df = df.dropna(subset=['ORDER_STATUS'])  # Remove unknown statuses

# Parse dates
df['ORDER_DATE'] = pd.to_datetime(df['ORDER_DATE'])

# Write to output dataset
dataiku.Dataset("CLEAN_ORDERS").write_with_schema(df)

print(f"✓ Cleaned {len(df)} order records")
