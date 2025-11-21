"""
Clean customer data from Snowflake

This recipe:
- Removes rows with missing critical fields
- Standardizes email addresses
- Formats customer IDs
- Validates data types
"""

import dataiku
import pandas as pd

# Read input dataset
df = dataiku.Dataset("RAW_CUSTOMERS").get_dataframe()

# Remove rows with missing critical fields
df = df.dropna(subset=['CUSTOMER_ID', 'EMAIL', 'CUSTOMER_NAME'])

# Standardize email addresses
df['EMAIL'] = df['EMAIL'].str.lower().str.strip()

# Format customer IDs (ensure they're strings)
df['CUSTOMER_ID'] = df['CUSTOMER_ID'].astype(str).str.strip()

# Standardize customer names
df['CUSTOMER_NAME'] = df['CUSTOMER_NAME'].str.strip()

# Handle missing states (default to 'UNKNOWN')
df['CUSTOMER_STATE'] = df['CUSTOMER_STATE'].fillna('UNKNOWN')

# Ensure uppercase for Snowflake compatibility
for col in df.columns:
    if col not in ['EMAIL']:  # Keep email lowercase
        if df[col].dtype == 'object':
            df[col] = df[col].str.upper()

# Write to output dataset
dataiku.Dataset("CLEAN_CUSTOMERS").write_with_schema(df)

print(f"✓ Cleaned {len(df)} customer records")
