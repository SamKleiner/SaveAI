# Sample program

import requests

# Backend API URL
BASE_URL = "http://localhost:8000"

# Sample Product Data
dummy_products = [
    {"name": "Milk", "sku": "123456789014", "cost_price": 1.00, "base_price": 2.50, "stock_quantity": 50, "description": "Fresh dairy milk"},
    {"name": "Banana", "sku": "123456789015", "cost_price": 1.20, "base_price": 3.00, "stock_quantity": 60, "description": "Fresh ripe banana"},
    {"name": "Orange Juice", "sku": "123456789016", "cost_price": 1.50, "base_price": 3.50, "stock_quantity": 40, "description": "Fresh squeezed orange juice"},
    {"name": "Apple", "sku": "123456789017", "cost_price": 1.00, "base_price": 2.20, "stock_quantity": 75, "description": "Crisp red apple"},
    {"name": "Bread", "sku": "123456789018", "cost_price": 1.80, "base_price": 4.00, "stock_quantity": 90, "description": "Whole wheat bread loaf"},
    {"name": "Eggs", "sku": "123456789019", "cost_price": 2.50, "base_price": 5.00, "stock_quantity": 120, "description": "Farm fresh eggs"},
    {"name": "Cheddar Cheese", "sku": "123456789020", "cost_price": 3.00, "base_price": 6.50, "stock_quantity": 50, "description": "Sharp aged cheddar cheese"},
    {"name": "Butter", "sku": "123456789021", "cost_price": 2.80, "base_price": 5.50, "stock_quantity": 45, "description": "Creamy salted butter"},
    {"name": "Chicken Breast", "sku": "123456789022", "cost_price": 5.00, "base_price": 10.50, "stock_quantity": 60, "description": "Fresh boneless chicken breast"},
    {"name": "Ground Beef", "sku": "123456789023", "cost_price": 4.50, "base_price": 9.00, "stock_quantity": 55, "description": "Lean ground beef"},
    {"name": "Salmon Fillet", "sku": "123456789024", "cost_price": 7.00, "base_price": 14.50, "stock_quantity": 30, "description": "Fresh Atlantic salmon fillet"},
    {"name": "Lettuce", "sku": "123456789025", "cost_price": 1.20, "base_price": 2.50, "stock_quantity": 70, "description": "Crispy green lettuce"},
    {"name": "Tomato", "sku": "123456789026", "cost_price": 1.50, "base_price": 3.20, "stock_quantity": 80, "description": "Fresh vine-ripened tomatoes"},
    {"name": "Cucumber", "sku": "123456789027", "cost_price": 1.00, "base_price": 2.20, "stock_quantity": 85, "description": "Cool and crisp cucumber"},
    {"name": "Potato", "sku": "123456789028", "cost_price": 1.30, "base_price": 3.00, "stock_quantity": 100, "description": "Starchy white potato"},
    {"name": "Carrot", "sku": "123456789029", "cost_price": 1.10, "base_price": 2.50, "stock_quantity": 95, "description": "Sweet fresh carrots"},
    {"name": "Onion", "sku": "123456789030", "cost_price": 1.00, "base_price": 2.00, "stock_quantity": 110, "description": "Pungent yellow onion"},
    {"name": "Garlic", "sku": "123456789031", "cost_price": 1.20, "base_price": 2.80, "stock_quantity": 90, "description": "Aromatic fresh garlic"},
    {"name": "Olive Oil", "sku": "123456789032", "cost_price": 5.00, "base_price": 10.00, "stock_quantity": 40, "description": "Extra virgin olive oil"},
    {"name": "Pasta", "sku": "123456789033", "cost_price": 2.00, "base_price": 4.50, "stock_quantity": 60, "description": "Durum wheat spaghetti"},
    {"name": "Rice", "sku": "123456789034", "cost_price": 3.00, "base_price": 6.00, "stock_quantity": 75, "description": "Long-grain white rice"},
    {"name": "Black Beans", "sku": "123456789035", "cost_price": 2.50, "base_price": 5.00, "stock_quantity": 65, "description": "Organic black beans"},
    {"name": "Canned Tuna", "sku": "123456789036", "cost_price": 2.80, "base_price": 5.50, "stock_quantity": 50, "description": "Canned light tuna in water"},
    {"name": "Yogurt", "sku": "123456789037", "cost_price": 2.20, "base_price": 4.80, "stock_quantity": 70, "description": "Greek yogurt, plain"},
    {"name": "Almond Milk", "sku": "123456789038", "cost_price": 3.00, "base_price": 6.00, "stock_quantity": 45, "description": "Unsweetened almond milk"},
    {"name": "Sarah's Peanut Butter", "sku": "123456789039", "cost_price": 3.50, "base_price": 1000.00, "stock_quantity": 50, "description": "Creamy peanut butter"},
    {"name": "Jam", "sku": "123456789040", "cost_price": 2.80, "base_price": 5.50, "stock_quantity": 55, "description": "Strawberry jam"},
    {"name": "Honey", "sku": "123456789041", "cost_price": 4.00, "base_price": 8.00, "stock_quantity": 40, "description": "Organic raw honey"},
    {"name": "Cereal", "sku": "123456789042", "cost_price": 3.00, "base_price": 6.50, "stock_quantity": 65, "description": "Whole grain breakfast cereal"},
    {"name": "Chocolate", "sku": "123456789043", "cost_price": 2.50, "base_price": 5.00, "stock_quantity": 70, "description": "Dark chocolate bar"},
    {"name": "Ice Cream", "sku": "123456789044", "cost_price": 4.50, "base_price": 9.00, "stock_quantity": 35, "description": "Vanilla bean ice cream"},
    {"name": "Coffee Beans", "sku": "123456789045", "cost_price": 6.00, "base_price": 12.00, "stock_quantity": 40, "description": "Premium Arabica coffee beans"},
    {"name": "Tea", "sku": "123456789046", "cost_price": 3.50, "base_price": 7.00, "stock_quantity": 55, "description": "Organic green tea"},
    {"name": "Toilet Paper", "sku": "123456789047", "cost_price": 5.00, "base_price": 10.50, "stock_quantity": 100, "description": "Soft 2-ply toilet paper"},
    {"name": "Dish Soap", "sku": "123456789048", "cost_price": 2.50, "base_price": 5.00, "stock_quantity": 60, "description": "Lemon-scented dish soap"},
]


def add_product(product):
    """Send a request to the FastAPI backend to add a product."""
    # In populate_db.py
    #response = requests.post(f"{BASE_URL}/products/", json=product)
    response = requests.post(f"{BASE_URL}/products/", params=product)
    
    if response.status_code == 200:
        print(f"✅ Added product: {product['name']} (SKU: {product['sku']})")
    else:
        print(f"❌ Failed to add {product['name']}: {response.text}")

if __name__ == "__main__":
    print("\n🚀 Populating database with dummy products...\n")
    
    for product in dummy_products:
        add_product(product)

    print("\n✅ Database population complete! You can now see products in the POS system.\n")
