# lambda_function.py
# PURPOSE: AWS Lambda handler - runs automatically on schedule
# DEPLOY:  Upload as lambda_deploy.zip to AWS Lambda

import os
import json
import boto3
import io

def lambda_handler(event, context):
    """
    AWS Lambda calls this function automatically every weekday at 9:30 AM.
    It downloads the latest 5 days of market data and saves to S3.
    """
    import yfinance as yf
    import pandas as pd

    SYMBOLS = ['AAPL', 'MSFT', 'GOOGL', 'BTC-USD', 'ETH-USD']

    # AWS credentials come from Lambda Environment Variables (not .env file)
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'us-east-1')
    )
    bucket = os.environ.get('S3_BUCKET_NAME', 'trading-raw-data-2024')

    results = []
    errors  = []

    for symbol in SYMBOLS:
        try:
            print(f'Fetching {symbol}...')
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='5d', interval='1d')
            if df.empty:
                errors.append(f'{symbol}: no data')
                continue
            df.reset_index(inplace=True)
            df['Symbol'] = symbol
            df['Date']   = df['Date'].astype(str)
            df = df[['Date','Open','High','Low','Close','Volume','Symbol']]
            # Upload to S3
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            folder = 'crypto' if '-USD' in symbol else 'stocks'
            s3.put_object(
                Bucket=bucket,
                Key=f'{folder}/{symbol}_latest.csv',
                Body=csv_buf.getvalue()
            )
            results.append(f'{symbol}: {len(df)} rows uploaded to S3')
            print(f'  OK: {symbol} - {len(df)} rows')
        except Exception as e:
            errors.append(f'{symbol}: {str(e)}')
            print(f'  ERROR: {symbol} - {e}')

    response_body = {
        'status':  'success' if not errors else 'partial',
        'results': results,
        'errors':  errors
    }
    print('Lambda complete:', json.dumps(response_body, indent=2))
    return {
        'statusCode': 200,
        'body': json.dumps(response_body)
    }
