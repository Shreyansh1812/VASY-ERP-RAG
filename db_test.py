from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Shreyu_12")

def test_connection():
    try:
        # Initialize the database driver
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        print(" Successfully connected")
        
        # Execute a test query to count the products we ingested earlier
        records, summary, keys = driver.execute_query(
            "MATCH (p:Product) RETURN count(p) AS product_count"
        )
        print(f"Verified: Graph contains {records[0]['product_count']} products.")
        
        driver.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()