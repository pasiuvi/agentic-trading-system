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
from sqlalchemy import create_engine

load_dotenv()

SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']

def fetch_stock_data(symbol, period='1y', interval='1d'):
    """Downloads historical price data for a given stock/crypto symbol."""
    print(f'  Downloading data for {symbol}...')
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)
    if df.empty:
        print(f'  WARNING: No data found for {symbol}. Skipping.')
        return None
    df.reset_index(inplace=True)
    df['Symbol'] = symbol
    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Symbol']]
    df['Date'] = df['Date'].astype(str)
    print(f'  Downloaded {len(df)} rows for {symbol}')
    return df

def upload_to_s3(df, symbol):
    """Uploads DataFrame as CSV to S3 bucket."""
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        folder = 'crypto' if '-USD' in symbol else 'stocks'
        s3.put_object(
            Bucket=os.getenv('S3_BUCKET_NAME'),
            Key=f'{folder}/{symbol}_data.csv',
            Body=csv_buffer.getvalue()
        )
        print(f'  Uploaded {symbol} to S3 bucket')
    except Exception as e:
        print(f'  S3 upload failed for {symbol}: {e}')

def save_to_rds(df):
    """Saves DataFrame to PostgreSQL RDS database."""
    try:
        conn_str = (
            f"postgresql://{os.getenv('RDS_USER')}:{os.getenv('RDS_PASSWORD')}"
            f"@{os.getenv('RDS_ENDPOINT')}/{os.getenv('RDS_DB')}"
        )
        engine = create_engine(conn_str)
        df.to_sql('market_data', engine, if_exists='append', index=False)
        print(f'  Saved {len(df)} rows to RDS database')
    except Exception as e:
        print(f'  RDS save failed: {e}')
        print('  (OK - S3 data is saved. RDS is optional bonus.)')

def save_locally(df, symbol):
    """Saves a copy to local data/ folder for EDA."""
    os.makedirs('data', exist_ok=True)
    path = f'data/{symbol}_data.csv'
    df.to_csv(path, index=False)
    print(f'  Saved locally to {path}')

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
