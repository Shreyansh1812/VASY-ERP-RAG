from neo4j import GraphDatabase
from langchain_ollama import OllamaLLM  # <-- Updated Library
from langchain_core.prompts import PromptTemplate

# 1. Database Credentials 
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Shreyu_12")

# 2. Initialize Connections
print("Initializing connections...")
driver = GraphDatabase.driver(URI, auth=AUTH)
llm = OllamaLLM(model="qwen2.5:3b") # <-- Updated Library syntax

# 3. Retrieve Data
def fetch_top_products():
    query = """
    MATCH (p:Product)
    RETURN p.name AS Product, p.category AS Category, p.price AS Price
    ORDER BY p.price DESC
    LIMIT 5
    """
    records, _, _ = driver.execute_query(query)
    context_string = "\n".join([f"Product: {r['Product']} | Category: {r['Category']} | Price: ${r['Price']}" for r in records])
    return context_string

# 4. Generate Answer
def generate_erp_answer(context, user_question):
    template = """
    You are a strict, factual ERP assistant. 
    Use ONLY the following structured data retrieved from our database to answer the user's question.
    If the answer is not contained in the data, say "I cannot find this in the current database."
    Do not make up any information.
    
    Database Context:
    {context}
    
    User Question: {question}
    
    Answer:
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    return chain.invoke({"context": context, "question": user_question})

if __name__ == "__main__":
    print("\n--- Diagnostic Check ---")
    diag_records, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS total")
    print(f"Total nodes Python can see: {diag_records[0]['total']}")

    print("\n--- Step 1: Querying Neo4j ---")
    db_context = fetch_top_products()  # <-- Updated function call
    print(f"Raw Data Extracted:\n{db_context}\n")
    
    # Updated Question
    question = "What are our top 5 most expensive products and their categories? Format the response as a bulleted list."
    print(f"--- Step 2: Asking Qwen ---")
    print(f"User Question: {question}\n")
    
    print("Waiting for Qwen to process...")
    final_answer = generate_erp_answer(db_context, question)
    
    print(f"\n--- Final Output ---")
    print(final_answer)
    
    driver.close()