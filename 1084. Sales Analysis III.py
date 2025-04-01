import pandas as pd

# Example DataFrames (assuming you already loaded these)
# product_df = pd.read_csv('Product.csv')
# sales_df = pd.read_csv('Sales.csv')

# Convert 'sale_date' to datetime
sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date'])

# Define date ranges
start_date = pd.Timestamp('2019-01-01')
end_date = pd.Timestamp('2019-03-31')

# Find products sold within Q1 2019
q1_sales = sales_df[
    (sales_df['sale_date'] >= start_date) &
    (sales_df['sale_date'] <= end_date)
]

# Find products sold outside Q1 2019
non_q1_sales = sales_df[
    (sales_df['sale_date'] < start_date) |
    (sales_df['sale_date'] > end_date)
]

# Identify product_ids sold exclusively in Q1 2019
exclusive_q1_products = set(q1_sales['product_id']) - set(non_q1_sales['product_id'])

# Filter the product DataFrame
result_df = product_df[product_df['product_id'].isin(exclusive_q1_products)][['product_id', 'product_name']]

# Display the result
print(result_df)

# or

import mysql.connector
import pandas as pd

# Connect to MySQL
conn = mysql.connector.connect(
    host='your_host',
    user='your_user',
    password='your_password',
    database='your_db'
)

query = """
Select distinct p.product_name, s.product_id
From Sales as s
Join Product as p on s.product_id = p.product_id
Where s.sale_date between '2019-01-01' and '2019-03-31'
and s.product_id not in (
Select product_id
From Sales
Where sale_date < '2019-01-01' or sale_date > '2019-03-31'
)
"""

result_df = pd.read_sql(query, conn)

print(result_df)

conn.close()
