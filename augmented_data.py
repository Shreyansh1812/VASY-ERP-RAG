import csv
import random
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURATION & SCALE
# ==========================================
NUM_CUSTOMERS = 1000
NUM_PRODUCTS = 500
NUM_ORDERS = 25000

# Base properties
INDUSTRIES = ["Retail", "Healthcare", "Finance", "Technology", "Manufacturing", "Education"]
REGIONS = ["Florida", "California", "New York", "Texas", "Illinois", "Washington"]
CATEGORIES = ["Electronics", "Furniture", "Office Supplies", "Software", "Hardware", "Services"]

# VasyERP Multi-Tenancy
COMPANIES = [101, 202, 305, 450]

def random_date(start_year=2025, end_year=2026):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    time_between_dates = end_date - start_date
    random_number_of_days = random.randrange(time_between_dates.days)
    return (start_date + timedelta(days=random_number_of_days)).strftime('%Y-%m-%d')

# VasyERP Trap #3: NaN Contamination Generator
def _maybe_nan(value, p=0.02):
    return "NaN" if random.random() < p else round(value, 2)

print(f"Generating Messy VasyERP Dataset (4-File Structure): {NUM_ORDERS} Orders...")

# ==========================================
# 2. GENERATE CUSTOMERS
# ==========================================
customers = []
for i in range(1, NUM_CUSTOMERS + 1):
    customers.append({
        "CustomerID": f"CUST_{i:04d}",
        "Name": f"Enterprise Corp {i}",
        "Industry": random.choice(INDUSTRIES),
        "Region": random.choice(REGIONS),
        "CompanyID": random.choice(COMPANIES), # VasyERP Multi-tenancy
        "GSTIN": f"27AAAAA0000A1Z{random.randint(1,9)}" if random.random() < 0.4 else "" # B2B vs B2C
    })

with open("customers.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
    writer.writeheader()
    writer.writerows(customers)

# ==========================================
# 3. GENERATE PRODUCTS
# ==========================================
products = []
for i in range(1, NUM_PRODUCTS + 1):
    products.append({
        "ProductID": f"PROD_{i:04d}",
        "ProductName": f"Tech Widget Model {i}",
        "Category": random.choice(CATEGORIES),
        "UnitPrice": _maybe_nan(random.uniform(10.0, 5000.0), 0.01), # VasyERP NaN Trap
        "StockQuantity": random.randint(0, 1000),
        "CompanyID": random.choice(COMPANIES)
    })

with open("products.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=products[0].keys())
    writer.writeheader()
    writer.writerows(products)

# ==========================================
# 4. GENERATE ORDERS & ORDER ITEMS
# ==========================================
orders = []
order_items = []
item_id_counter = 1

for i in range(1, NUM_ORDERS + 1):
    order_id = f"ORD_{i:05d}"
    cid = random.choice(COMPANIES)
    
    # VasyERP Trap #4 & #6: Types & Merchant Gate
    if cid == 450:
        order_type = "pos" if random.random() < 0.92 else random.choice(["posreturn", "creditnote"])
    else:
        order_type = random.choices(["invoice", "pos", "creditnote", "posreturn"], weights=[55, 30, 8, 7])[0]
        
    # VasyERP Trap #5: Walk-in POS (Null CustomerID)
    customer_id = ""
    if not (order_type == "pos" and random.random() < 0.30):
        # Pick a customer that belongs to this specific CompanyID
        valid_customers = [c["CustomerID"] for c in customers if c["CompanyID"] == cid]
        if valid_customers: customer_id = random.choice(valid_customers)

    # VasyERP Trap #2: Soft Delete Flag
    is_deleted = 1 if random.random() < 0.05 else 0
    
    # VasyERP Trap #7: Schema Typos
    billing_compny_name = f"B2B Co {i}" if customer_id and random.random() < 0.5 else ""

    orders.append({
        "OrderID": order_id,
        "CustomerID": customer_id,
        "OrderDate": random_date(),
        "Status": random.choices(["Completed", "Pending", "Shipped", "Cancelled"], weights=[70, 15, 10, 5])[0],
        "CompanyID": cid,
        "OrderType": order_type,
        "IsDeleted": is_deleted,
        "BillingCompnyName": billing_compny_name # Intentional Typo
    })
    
    # Generate 1 to 4 Order Items
    num_items = random.randint(1, 4)
    selected_products = random.sample(products, num_items)
    
    for prod in selected_products:
        qty = random.randint(1, 20)
        
        # If return or credit note, make quantity mathematically negative
        if order_type in ["posreturn", "creditnote"]:
            qty = -qty
            
        raw_price = prod["UnitPrice"] if prod["UnitPrice"] != "NaN" else 100.0
        line_total = qty * raw_price
        
        order_items.append({
            "OrderItemID": f"ITEM_{item_id_counter:06d}",
            "OrderID": order_id,
            "ProductVarientID": prod["ProductID"], # Intentional Typo (Maps to ProductID)
            "Quantity": qty,
            "LineTotal": _maybe_nan(line_total, 0.02) # VasyERP NaN Trap
        })
        item_id_counter += 1

with open("orders.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=orders[0].keys())
    writer.writeheader()
    writer.writerows(orders)

with open("order_items.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
    writer.writeheader()
    writer.writerows(order_items)

print(f"✅ VasyERP 4-File Generation Complete! Generated {len(order_items)} edges with intentional typos, NaNs, and missing links.")