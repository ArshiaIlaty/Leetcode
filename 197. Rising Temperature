from sqlalchemy import create_engine, text
import pandas as pd

# Create database engine
# For SQLite:
engine = create_engine('sqlite:///your_database.db')

# For MySQL:
# engine = create_engine('mysql+pymysql://username:password@host/dbname')

# For PostgreSQL:
# engine = create_engine('postgresql+psycopg2://username:password@host/dbname')

# Your SQL query as a text string
query = text("""
Select w1.id
From Weather as w1, Weather as w2
Where dateDiff(w1.recordDate,w2.recordDate) = 1 AND w1.Temperature > w2.Temperature;
""")

# Execute the query using pandas for easy DataFrame handling
with engine.connect() as connection:
    result_df = pd.read_sql_query(query, connection)

# Display the result
print(result_df)
