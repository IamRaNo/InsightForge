import pandas as pd
from sqlalchemy import create_engine

# ---- MySQL credentials (fill these in) ----
DB_USER = "root"
DB_PASSWORD = "7003890541"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "ipo_prices"
# --------------------------------------------

# File paths
ipo_path = r"C:\Users\Rano's PC\Machine\InsightForge\InsightForge\Avoiding The Hype Trap\_datasets\_engineered_data\ipo.csv"
prices_path = r"C:\Users\Rano's PC\Machine\InsightForge\InsightForge\Avoiding The Hype Trap\_datasets\_engineered_data\prices.csv"

# Load CSVs
ipo = pd.read_csv(ipo_path)
ipo.columns = ipo.columns.str.strip()   # removes stray spaces from column names

prices = pd.read_csv(prices_path)
prices.columns = prices.columns.str.strip() 

# Create MySQL connection
engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Upload tables (replace if they already exist)
ipo.to_sql('ipo', con=engine, if_exists='replace', index=False)
prices.to_sql('prices', con=engine, if_exists='replace', index=False)

print("Upload complete.")
print(f"ipo table: {len(ipo)} rows")
print(f"prices table: {len(prices)} rows")