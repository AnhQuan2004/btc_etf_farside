import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os
import random
from flask import Flask, jsonify, request

# Create Flask app
app = Flask(__name__)

def scrape_bitcoin_etf_data(url):
    """Scrape Bitcoin ETF data from the specified URL using BeautifulSoup."""
    
    # Create a session for better handling
    session = requests.Session()
    
    # More comprehensive headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    session.headers.update(headers)
    
    try:
        # Add a small random delay to seem more human-like
        time.sleep(random.uniform(1, 3))
        
        # Make the request with session
        response = session.get(url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        print("Website loaded successfully!")
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Define the headers
        table_headers = ['Date', 'IBIT', 'FBTC', 'BITB', 'ARKB', 'BTCO', 'EZBC', 'BRRR', 'HODL', 'BTCW', 'GBTC', 'BTC', 'Total']
        data = []
        
        # Find the table with class 'etf'
        table = soup.find('table', class_='etf')
        if not table:
            print("Table with class 'etf' not found")
            return None, None
        
        # Find all rows in the table
        rows = table.find_all('tr')
        if not rows:
            print("No rows found in table")
            return None, None
        
        # Skip the header row and process data rows
        for row in rows[1:]:  # Skip header row
            # Find all td elements in the row
            cells = row.find_all('td')
            if cells:
                # Create a list for this row's data
                row_data = []
                
                # Extract text from each cell (should correspond to our headers)
                for i, cell in enumerate(cells):
                    if i < len(table_headers):  # Ensure we don't exceed our header count
                        # Look for span with class 'tabletext' inside the cell
                        span = cell.find('span', class_='tabletext')
                        if span:
                            row_data.append(span.get_text().strip())
                        else:
                            # If no span, get the cell text directly
                            row_data.append(cell.get_text().strip())
                
                # Only add rows that have the right number of columns
                if len(row_data) == len(table_headers):
                    data.append(row_data)
        
        if not data:
            print("No data found in table")
            return None, None
            
        return table_headers, data
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print(f"Error: Access forbidden (403). Website may be blocking automated requests.")
        else:
            print(f"HTTP Error: {e}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None, None
    except Exception as e:
        print(f"Error during scraping: {e}")
        return None, None
    finally:
        session.close()

def process_data(headers, data):
    """Process the scraped data and return as JSON without saving to files."""
    if headers and data:
        # Create a list of dictionaries, each representing a row
        json_data = []
        for row in data:
            # Create a dictionary with header:value pairs
            row_dict = {headers[i]: value for i, value in enumerate(row)}
            json_data.append(row_dict)
        
        # Print sample data to console (first 3 rows)
        print(f"Sample data (first 3 rows):")
        for i, row in enumerate(json_data[:3]):
            print(f"Row {i+1}: {row}")
        
        # Print summary
        print(f"Total rows processed: {len(data)}")
        
        return json_data
    else:
        print("No data to process")
        return None

# Flask routes
@app.route('/')
def home():
    """Home page with basic information."""
    return jsonify({
        "message": "Bitcoin ETF Flow Scraper API",
        "endpoints": {
            "/": "This page",
            "/scrape": "Scrape and return Bitcoin ETF flow data",
            "/health": "Health check"
        }
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "bitcoin-etf-scraper"})

@app.route('/scrape')
def scrape_endpoint():
    """Scrape Bitcoin ETF data and return as JSON for display."""
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data"
    
    print(f"Scraping data from: {url}")
    print("Starting Bitcoin ETF data scraper...")
    
    # Try multiple times with different delays
    max_retries = 3
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} of {max_retries}")
        
        headers, data = scrape_bitcoin_etf_data(url)
        
        if headers and data:
            json_data = process_data(headers, data)
            print("✅ Scraping completed successfully!")
            
            return jsonify({
                "status": "success",
                "message": "Bitcoin ETF Flow Data",
                "source": "farside.co.uk",
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_records": len(data),
                "columns": headers,
                "data": json_data
            })
        else:
            if attempt < max_retries - 1:
                wait_time = random.uniform(5, 10)
                print(f"❌ Attempt {attempt + 1} failed. Retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                print("❌ All attempts failed")
    
    return jsonify({
        "status": "error",
        "message": "Unable to fetch Bitcoin ETF data",
        "suggestion": "Website may be temporarily unavailable. Please try again later."
    }), 500

def main():
    """Main function to run the scraping process with BeautifulSoup."""
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data"
    
    print(f"Scraping data from: {url}")
    print("Starting Bitcoin ETF data scraper...")
    
    headers, data = scrape_bitcoin_etf_data(url)
    
    if headers and data:
        process_data(headers, data)
        print("✅ Scraping completed successfully!")
    else:
        print("❌ Failed to scrape data")

if __name__ == "__main__":
    # Get port from environment variable for Cloud Run
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)