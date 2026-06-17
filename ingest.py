import csv
from neo4j import GraphDatabase

# 1. Database Credentials & Local Paths
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Shreyu_12")
BASE_PATH = r"C:\Users\shrey\Downloads\Internship_2026"

def read_csv(filename):
    """Reads a local CSV file into Python memory."""
    filepath = f"{BASE_PATH}\\{filename}"
    with open(filepath, mode='r', encoding='utf-8-sig') as file:
        return list(csv.DictReader(file))

# 2. The Ingestion Functions
def ingest_customers(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.CustomerID IS NOT NULL
    MERGE (c:Customer {id: row.CustomerID})
    SET c.name = row.Name, 
        c.industry = row.Industry, 
        c.region = row.Region;
    """
    tx.run(query, batch=data)

def ingest_products(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.ProductID IS NOT NULL
    MERGE (p:Product {id: row.ProductID})
    SET p.name = row.ProductName,
        p.category = row.Category,
        p.price = toFloat(row.UnitPrice),
        p.stock = toInteger(row.StockQuantity);
    """
    tx.run(query, batch=data)

def ingest_orders(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.OrderID IS NOT NULL
    MERGE (o:Order {id: row.OrderID})
    SET o.date = row.OrderDate, 
        o.status = row.Status
    WITH row, o
    MATCH (c:Customer {id: row.CustomerID})
    MERGE (c)-[:PLACED]->(o);
    """
    tx.run(query, batch=data)

def ingest_order_items(tx, data):
    query = """
    UNWIND $batch AS row
    WITH row WHERE row.OrderID IS NOT NULL AND row.ProductID IS NOT NULL
    MATCH (o:Order {id: row.OrderID})
    MATCH (p:Product {id: row.ProductID})
    MERGE (o)-[rel:CONTAINS]->(p)
    SET rel.quantity = toInteger(row.Quantity),
        rel.lineTotal = toFloat(row.LineTotal);
    """
    tx.run(query, batch=data)

# 3. Execution Engine
if __name__ == "__main__":
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    
    with driver.session() as session:
        # Wipe the database clean to ensure no bad data from previous attempts
        print("Wiping existing database...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Ingesting Customers...")
        customers_data = read_csv("customers.csv")
        session.execute_write(ingest_customers, customers_data)

        print("Ingesting Products...")
        products_data = read_csv("products.csv")
        session.execute_write(ingest_products, products_data)

        print("Ingesting Orders & Connections...")
        orders_data = read_csv("orders.csv")
        session.execute_write(ingest_orders, orders_data)

        print("Ingesting Order Items (Relationships)...")
        items_data = read_csv("order_items.csv")
        session.execute_write(ingest_order_items, items_data)

    driver.close()
    print("✅ Full Database Ingestion Complete! You bypassed the Sandbox.")