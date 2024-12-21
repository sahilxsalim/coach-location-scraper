import requests
import json
from typing import List, Dict
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class CoachOutletScraper:
    def __init__(self, store_name: str, zip_code: str):
        self.store_name = store_name
        self.zip_code = zip_code
        self.base_url = "https://www.coachoutlet.com/api"
        self.available_products: List[Dict] = []
        logging.info(f"Initializing scraper for store: {store_name} with zip code: {zip_code}")

    def get_products_page(self, page: int) -> dict:
        """Fetch products from a specific page"""
        # url = f"{self.base_url}/get-shop/wallets/large-wallets"
        url = f"{self.base_url}/get-shop/wallets/small-wallets"
        params = {
            "gender": "Women",
            "page": page
        }
        
        try:
            logging.info(f"Fetching products from page {page}")
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            products_count = len(data.get("pageData", {}).get("products", []))
            logging.info(f"Successfully retrieved {products_count} products from page {page}")
            return data
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching page {page}: {str(e)}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON from page {page}: {str(e)}")
            return {}

    def check_store_availability(self, product_id: str) -> bool:
        """Check if a product is available at the specified store"""
        url = f"{self.base_url}/stores/get-stores"
        params = {
            "products": product_id,
            "zipCode": self.zip_code
        }
        
        try:
            logging.debug(f"Checking availability for product {product_id}")
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Find the specified store in the results
            for store in data.get("stores", []):
                if store["name"] == self.store_name:
                    availability = store.get("storeAvailability", [{}])[0]
                    is_available = availability.get("IN_STOCK", False)
                    logging.debug(f"Product {product_id} availability at {self.store_name}: {is_available}")
                    return is_available
            
            logging.warning(f"Store {self.store_name} not found in results for product {product_id}")
            return False
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error checking availability for product {product_id}: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON for product {product_id}: {str(e)}")
            return False

    def scrape_available_products(self) -> List[Dict]:
        """Scrape all available products at the specified store"""
        try:
            # Get first page to determine total pages
            first_page = self.get_products_page(1)
            total_pages = first_page.get("pageData", {}).get("totalPages", 1)
            logging.info(f"Found {total_pages} total pages to process")
            
            # Process all pages
            for page in range(1, total_pages + 1):
                logging.info(f"Processing page {page} of {total_pages}...")
                
                # Get products from current page
                page_data = self.get_products_page(page)
                products = page_data.get("pageData", {}).get("products", [])
                
                # Check each product's availability
                for idx, product in enumerate(products, 1):
                    try:
                        # Get product details
                        product_id = product.get("defaultVariant", {}).get("productId")
                        if not product_id:
                            logging.warning(f"No product ID found for item {idx} on page {page}")
                            continue
                        
                        # Check availability
                        if self.check_store_availability(product_id):
                            product_info = {
                                "name": product.get("name", ""),
                                "id": product_id,
                                "url": f"https://www.coachoutlet.com{product.get('url', '')}",
                                "price": product.get("defaultVariant", {}).get("prices", {}).get("currentPrice")
                            }
                            self.available_products.append(product_info)
                            logging.info(f"Found available product: {product_info['name']} ({product_info['id']})")
                        
                        # Add a small delay to avoid overwhelming the server
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logging.error(f"Error processing product {idx} on page {page}: {str(e)}")
                        continue
                
                logging.info(f"Completed processing page {page}")
            
            logging.info(f"Scraping completed. Found {len(self.available_products)} available products")
            return self.available_products
            
        except Exception as e:
            logging.error(f"Fatal error during scraping: {str(e)}")
            return self.available_products

def main():
    try:
        # Initialize scraper with store name and zip code
        scraper = CoachOutletScraper(
            store_name="Milpitas",
            zip_code="95035"
        )
        
        # Get available products
        available_products = scraper.scrape_available_products()
        
        # Print results
        print("\nAvailable Products at", scraper.store_name)
        print("-" * 50)
        for product in available_products:
            print(f"Name: {product['name']}")
            print(f"ID: {product['id']}")
            print(f"Price: ${product['price']}")
            print(f"URL: {product['url']}")
            print("-" * 50)
        
        logging.info(f"Total available products: {len(available_products)}")
        print(f"\nTotal available products: {len(available_products)}")
        
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print("An error occurred. Check the log file for details.")

if __name__ == "__main__":
    main()