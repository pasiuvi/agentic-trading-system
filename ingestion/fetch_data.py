# ingestion/fetch_data.py
# PURPOSE: Download stock/crypto price data and save to AWS S3 and RDS database
# USAGE:   python ingestion/fetch_data.py

import yfinance as yf
import pandas as pd
import boto3
import os
import io
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load secret keys from .env file
load_dotenv()

# ── Symbols to track ─────────────────────────────────────────────────────
# Add or remove symbols here. -USD means crypto.
SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']


# ── Function 1: Download data from Yahoo Finance ──────────────────────────
def fetch_stock_data(symbol, period='1y', interval='1d'):
    """
    Downloads historical price data for a given stock/crypto symbol.
    period = how far back ('1y' = 1 year, '6mo' = 6 months)
    interval = candle size ('1d' = daily, '1h' = hourly)
    """
    print(f'  Downloading data for {symbol}...')
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        print(f'  WARNING: No data found for {symbol}. Skipping.')
        return None

    # Reset index so Date becomes a regular column
    df.reset_index(inplace=True)

    # Add symbol column so we know which stock each row belongs to
    df['Symbol'] = symbol

    # Keep only the columns we need
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']]

    # Convert Date to string (easier to store)
    df['Date'] = df['Date'].astype(str)

    print(f'  Downloaded {len(df)} rows for {symbol}')
    return df


# ── Function 2: Upload raw CSV to AWS S3 ─────────────────────────────────
def upload_to_s3(df, symbol):
    """
    Uploads a DataFrame as a CSV file to the S3 bucket.
    File path in S3 will be: stocks/AAPL_data.csv
    """
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )

        # Convert DataFrame to CSV string (not a file on disk)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)

        # Decide folder based on symbol type
        folder = 'crypto' if '-USD' in symbol else 'stocks'

        s3.put_object(
            Bucket=os.getenv('S3_BUCKET_NAME'),
            Key=f'{folder}/{symbol}_data.csv',
            Body=csv_buffer.getvalue()
        )
        print(f'  Uploaded {symbol} to S3 bucket')

    except Exception as e:
        print(f'  S3 upload failed for {symbol}: {e}')


# ── Function 3: Save to RDS PostgreSQL database ───────────────────────────
def save_to_rds(df):
    """
    Saves the DataFrame into a PostgreSQL table called 'market_data'.
    Creates the table automatically if it does not exist.
    """
    try:
        # Build database connection string
        conn_str = (
            f"postgresql://{os.getenv('RDS_USER')}:{os.getenv('RDS_PASSWORD')}"
            f"@{os.getenv('RDS_ENDPOINT')}/{os.getenv('RDS_DB')}"
        )
        engine = create_engine(conn_str)

        # Save to database — if table exists, append new rows
        df.to_sql('market_data', engine, if_exists='append', index=False)
        print(f'  Saved {len(df)} rows to RDS database')

    except Exception as e:
        print(f'  RDS save failed: {e}')
        print('  (This is OK for now — S3 data is saved)')


# ── Also save locally for EDA ────────────────────────────────────────────
def save_locally(df, symbol):
    """Saves a copy to local data/ folder for the EDA step."""
    os.makedirs('data', exist_ok=True)
    path = f'data/{symbol}_data.csv'
    df.to_csv(path, index=False)
    print(f'  Saved locally to {path}')


# ── Main: Run for all symbols ─────────────────────────────────────────────
if __name__ == '__main__':
    print('=== DATA COLLECTION STARTED ===')
    for symbol in SYMBOLS:
        print(f'\nProcessing: {symbol}')
        df = fetch_stock_data(symbol)
        if df is not None:
            upload_to_s3(df, symbol)
            save_to_rds(df)
            save_locally(df, symbol)
    print('\n=== DATA COLLECTION COMPLETE ===')
