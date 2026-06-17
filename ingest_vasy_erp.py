import csv
from neo4j import GraphDatabase

# ==========================================
# 1. CONFIGURATION & CONNECTIONS
# ==========================================
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Shreyu_12")
BASE_PATH = r"C:\Users\shrey\Downloads\Internship_2026"

def read_and_scrub_csv(filename):
    """Reads CSV and scrubs VasyERP 'NaN' traps before they hit the database."""
    filepath = f"{BASE_PATH}\\{filename}"
    data = []
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Trap Defense: Convert "NaN" strings to Python None (Null)
            for key, value in row.items():
                if value == "NaN":
                    row[key] = None
            data.append(row)
    return data

# ==========================================
# 2. THE DEFENSIVE CYPHER QUERIES
# ==========================================
def ingest_customers(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.CustomerID IS NOT NULL AND row.CustomerID <> ""
    MERGE (c:Customer {id: row.CustomerID})
    SET c.name = row.Name, 
        c.industry = row.Industry, 
        c.region = row.Region,
        c.company_id = toInteger(row.CompanyID),
        c.gstin = row.GSTIN;
    """
    tx.run(query, batch=data)

def ingest_products(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.ProductID IS NOT NULL AND row.ProductID <> ""
    MERGE (p:Product {id: row.ProductID})
    SET p.name = row.ProductName,
        p.category = row.Category,
        p.price = toFloat(row.UnitPrice),
        p.stock = toInteger(row.StockQuantity),
        p.company_id = toInteger(row.CompanyID);
    """
    tx.run(query, batch=data)

def ingest_orders(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.OrderID IS NOT NULL AND row.OrderID <> ""
    
    // Create the Order Node
    MERGE (o:Order {id: row.OrderID})
    SET o.date = row.OrderDate, 
        o.status = row.Status,
        o.type = row.OrderType,
        o.company_id = toInteger(row.CompanyID),
        o.is_deleted = toInteger(row.IsDeleted),
        o.billing_company_name = row.BillingCompnyName // Mapping the typo
        
    // Trap Defense: Only draw relationship IF CustomerID exists (Skips Walk-in POS)
    WITH row, o
    WHERE row.CustomerID IS NOT NULL AND row.CustomerID <> ""
    MATCH (c:Customer {id: row.CustomerID})
    MERGE (c)-[:PLACED]->(o);
    """
    tx.run(query, batch=data)

def ingest_order_items(tx, data):
    query = """
    UNWIND $batch AS row
    // Mapping the ProductVarientID typo directly to our relationships
    WITH row WHERE row.OrderID IS NOT NULL AND row.ProductVarientID IS NOT NULL
    
    MATCH (o:Order {id: row.OrderID})
    MATCH (p:Product {id: row.ProductVarientID})
    MERGE (o)-[rel:CONTAINS]->(p)
    SET rel.quantity = toInteger(row.Quantity),
        rel.lineTotal = toFloat(row.LineTotal);
    """
    tx.run(query, batch=data)

# ==========================================
# 3. EXECUTION ENGINE
# ==========================================
if __name__ == "__main__":
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    with driver.session() as session:
        print("Wiping existing database to prepare for VasyERP data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Ingesting Customers...")
        customers_data = read_and_scrub_csv("customers.csv")
        session.execute_write(ingest_customers, customers_data)

        print("Ingesting Products...")
        products_data = read_and_scrub_csv("products.csv")
        session.execute_write(ingest_products, products_data)

        print("Ingesting Orders & Connections (This handles Walk-in POS)...")
        orders_data = read_and_scrub_csv("orders.csv")
        session.execute_write(ingest_orders, orders_data)

        print("Ingesting Order Items (Mapping Typos and Returns)...")
        items_data = read_and_scrub_csv("order_items.csv")
        session.execute_write(ingest_order_items, items_data)

    driver.close()
    print(" Full VasyERP Database Ingestion Complete! Defense protocols held.")