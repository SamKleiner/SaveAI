import requests
import random
import time

# Backend API URL
BASE_URL = "http://localhost:8000"

def create_sale(customer_id=None):
    url = f"{BASE_URL}/sales/"
    params = {}
    if customer_id is not None:
        params["customer_id"] = customer_id
    response = requests.post(url, params=params)
    if response.status_code == 200:
        sale = response.json()
        print(f"✅ Created sale with ID: {sale['id']}")
        return sale["id"]
    else:
        print(f"❌ Error creating sale: {response.text}")
        return None

def add_item_to_sale(sale_id, product_id, quantity):
    url = f"{BASE_URL}/sales/{sale_id}/add-item"
    params = {"product_id": product_id, "quantity": quantity}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        sale_item = response.json()
        print(f"✅ Added item: Product ID {product_id} x {quantity} to sale {sale_id}")
    else:
        print(f"❌ Error adding item to sale {sale_id}: {response.text}")

def get_products():
    url = f"{BASE_URL}/products/"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print("❌ Error fetching products.")
        return []

if __name__ == "__main__":
    products = get_products()
    if not products:
        print("No products found. Make sure your database is populated.")
        exit(1)

    num_sales_to_create = 10  # Adjust this number as needed

    for _ in range(num_sales_to_create):
        sale_id = create_sale()
        if sale_id is None:
            continue
        
        # Randomly add 1 to 5 items per sale
        num_items = random.randint(1, 5)
        for _ in range(num_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            add_item_to_sale(sale_id, product["id"], quantity)
        
        # Optionally, pause between sales to simulate time passing
        time.sleep(random.uniform(0.5, 2.0))
    
    print("✅ Finished simulating sales.")
