import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ==========================================
# 1. CONFIGURATION & CONNECTIONS
# ==========================================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

print("Initializing local AI and Database connections...")

# Initialize the LLM (The Reasoning Engine)
llm = OllamaLLM(model="qwen2.5:3b", temperature=0)

# Initialize the Graph Connection (The Memory/Database)
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# ... [Rest of the script remains exactly the same] ...
# ==========================================
# 2. THE FEW-SHOT GUARDRAILS (VASY ERP TUNED)
# ==========================================
cypher_template = """
You are an expert graph database translator for an ERP system. 
Your job is to translate the user's natural language question into a precise Neo4j Cypher query.

Strict Rules:
1. ONLY use the nodes, relationships, and properties provided in the schema below.
2. ALWAYS check for the `is_deleted` flag on Orders. Assume the user only wants active orders (is_deleted = 0) unless they specify otherwise.
3. If the user asks for "revenue" or "sales", you should SUM the `lineTotal` property on the `CONTAINS` relationship.
4. CRITICAL: When the user asks for "Company X", they are referring to the integer property `company_id: X` on the Order or Product node. DO NOT confuse this with the Customer `id` property (which is a string like "CUST_0001").
5. Your output must ONLY contain the Cypher query code. Do not explain the code. Do not add markdown blocks like ```cypher.

Database Schema:
{schema}

Here are a few examples to guide you:

Example 1: Multi-Tenancy & Revenue Aggregation
Question: What is the total active revenue for Company 450?
Cypher: MATCH (o:Order {{company_id: 450, is_deleted: 0}})-[rel:CONTAINS]->(p:Product) RETURN sum(rel.lineTotal) AS TotalRevenue

Example 2: Complex Joins (Customer -> Order -> Product)
Question: Which product category generated the most revenue from the Healthcare industry?
Cypher: MATCH (c:Customer {{industry: 'Healthcare'}})-[:PLACED]->(o:Order {{is_deleted: 0}})-[rel:CONTAINS]->(p:Product) RETURN p.category, sum(rel.lineTotal) AS Revenue ORDER BY Revenue DESC LIMIT 1

Example 3: Handling Typos & Company filtering
Question: What is the revenue for Company 202 from the Electronics category?
Cypher: MATCH (o:Order {{company_id: 202, is_deleted: 0}})-[rel:CONTAINS]->(p:Product {{category: 'Electronics'}}) RETURN sum(rel.lineTotal) AS TotalRevenue

Now, translate the following question:
Question: {question}
Cypher:
"""

# --> THIS WAS THE MISSING LINE <--
cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"], 
    template=cypher_template
)

# ==========================================
# 3. THE SYNTHESIS GUARDRAILS (QA PROMPT)
# ==========================================
qa_template = """
You are an expert ERP assistant. Use ONLY the following raw database output to answer the user's question.
The data is provided in a Python dictionary format. Extract the relevant names and numbers to form a clear, conversational sentence.

Database Output:
{context}

User Question: {question}

Final Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=qa_template
)

# ==========================================
# 4. BUILD THE RAG CHAIN (THE ORCHESTRATOR)
# ==========================================
qa_chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True, 
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,  
    allow_dangerous_requests=True 
)

# ==========================================
# 5. EXECUTION SYSTEM (INTERACTIVE CHAT)
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 VasyERP Graph RAG Agent Online")
    print("Type 'exit' or 'quit' to end the session.")
    print("="*50 + "\n")
    
    # Start the continuous chat loop
    while True:
        try:
            # 1. Get dynamic user input
            user_question = input("🧑‍💼 You: ")
            
            # 2. Check for exit commands
            if user_question.lower() in ['exit', 'quit', 'q']:
                print("\nShutting down the ERP Assistant. Goodbye! 👋\n")
                break
                
            # Skip empty inputs
            if not user_question.strip():
                continue
                
            print("🧠 Agent is thinking (Generating Cypher & Synthesizing)...\n")
            
            # 3. Invoke the chain dynamically
            response = qa_chain.invoke({"query": user_question})
            
            # 4. Print the final synthesized answer
            print("\n" + "="*50)
            print("🤖 Agent:")
            print(response["result"])
            print("="*50 + "\n")
            
        except Exception as e:
            # If a query fails, catch the error so the loop doesn't crash
            print(f"\n❌ Pipeline Failed for this query. Error: {e}\n")
            print("Let's try another question.\n")