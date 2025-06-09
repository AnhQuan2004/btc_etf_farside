import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os
from flask import Flask, jsonify, request

# Create Flask app
app = Flask(__name__)

def scrape_bitcoin_etf_data(url):
    """Scrape Bitcoin ETF data from the specified URL using BeautifulSoup."""
    
    # Set headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
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
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None, None
    except Exception as e:
        print(f"Error during scraping: {e}")
        return None, None

def save_to_json(headers, data, filename='bitcoin_etf_flows.json'):
    """Save the scraped data to a JSON file."""
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
        
        # Ensure output directory exists
        output_dir = '/app/output'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save to JSON file in output directory
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)
        
        print(f"\nData has been saved to {filepath}")
        
        # Print summary
        print(f"Total rows saved to JSON: {len(data)}")
        
        # Also save a CSV version for easier viewing
        csv_filename = filename.replace('.json', '.csv')
        csv_filepath = os.path.join(output_dir, csv_filename)
        df = pd.DataFrame(json_data)
        df.to_csv(csv_filepath, index=False)
        print(f"CSV version saved to {csv_filepath}")
        
        return json_data
    else:
        print("No data to save")
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
    """Scrape Bitcoin ETF data and return as JSON."""
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data"
    
    print(f"Scraping data from: {url}")
    print("Starting Bitcoin ETF data scraper...")
    
    headers, data = scrape_bitcoin_etf_data(url)
    
    if headers and data:
        json_data = save_to_json(headers, data)
        print("✅ Scraping completed successfully!")
        
        return jsonify({
            "status": "success",
            "message": "Bitcoin ETF data scraped successfully",
            "total_rows": len(data),
            "data": json_data
        })
    else:
        print("❌ Failed to scrape data")
        return jsonify({
            "status": "error",
            "message": "Failed to scrape Bitcoin ETF data"
        }), 500

def main():
    """Main function to run the scraping process with BeautifulSoup."""
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data"
    
    print(f"Scraping data from: {url}")
    print("Starting Bitcoin ETF data scraper...")
    
    headers, data = scrape_bitcoin_etf_data(url)
    
    if headers and data:
        save_to_json(headers, data)
        print("✅ Scraping completed successfully!")
    else:
        print("❌ Failed to scrape data")

if __name__ == "__main__":
    # Get port from environment variable for Cloud Run
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)