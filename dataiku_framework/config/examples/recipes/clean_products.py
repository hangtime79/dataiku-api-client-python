"""
Clean product data from Snowflake

This recipe:
- Removes duplicate products
- Standardizes product categories
- Validates prices
- Ensures data quality
"""

import dataiku
import pandas as pd

# Read input dataset
df = dataiku.Dataset("RAW_PRODUCTS").get_dataframe()

# Remove duplicates (keep latest)
df = df.sort_values('UPDATED_AT', ascending=False)
df = df.drop_duplicates(subset=['PRODUCT_ID'], keep='first')

# Remove rows with missing critical fields
df = df.dropna(subset=['PRODUCT_ID', 'PRODUCT_NAME', 'PRODUCT_PRICE'])

# Validate prices (must be positive)
df = df[df['PRODUCT_PRICE'] > 0]

# Ensure proper data types
df['PRODUCT_ID'] = df['PRODUCT_ID'].astype(str).str.strip()
df['PRODUCT_PRICE'] = df['PRODUCT_PRICE'].astype(float)

# Standardize product names and categories
df['PRODUCT_NAME'] = df['PRODUCT_NAME'].str.strip().str.upper()
df['PRODUCT_CATEGORY'] = df['PRODUCT_CATEGORY'].str.strip().str.upper()

# Handle missing categories
df['PRODUCT_CATEGORY'] = df['PRODUCT_CATEGORY'].fillna('UNCATEGORIZED')

# Write to output dataset
dataiku.Dataset("CLEAN_PRODUCTS").write_with_schema(df)

print(f"✓ Cleaned {len(df)} product records")
