import pandas as pd

# Full path to the CSV file
csv_path = r'C:\Users\ferna\Downloads\TCGplayer__MyPricing_20260326_063810.csv'

# Read the CSV file
df = pd.read_csv(csv_path)

# Sort by 'Total Quantity' column in descending order (highest first)
df_sorted = df.sort_values(by='Total Quantity', ascending=False)

# Save the sorted data to a new CSV file in the current directory
output_path = 'TCGplayer_sorted_by_total_quantity.csv'
df_sorted.to_csv(output_path, index=False)

print(f"Sorted CSV saved to: {output_path}")

# Print top 10 rows highlighting Total Quantity
print("\nTop 10 rows with highest Total Quantity (key columns):")
key_columns = ['Product Name', 'Set Name', 'Condition', 'Total Quantity', 'TCG Low Price', 'TCG Market Price']
print(df_sorted[key_columns].head(10).to_string(index=False))

print("\nFull top 10 rows:")
print(df_sorted.head(10))

# Summary including Total Quantity stats
print(f"\nSummary:")
print(f"Total rows: {len(df)}")
print(f"Max Total Quantity: {df['Total Quantity'].max()}")
print(f"Min Total Quantity: {df['Total Quantity'].min()}")
print(f"Average Total Quantity: {df['Total Quantity'].mean():.2f}")
