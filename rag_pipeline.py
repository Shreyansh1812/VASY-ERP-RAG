import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
# ==========================================
# 1. CONFIGURATION & CONNECTIONS
# ==========================================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Shreyu_12"

print("Initializing local AI and Database connections...")

# Initialize the LLM (The Reasoning Engine)
llm = OllamaLLM(model="qwen2.5:3b", temperature=0) # Temperature 0 ensures factual, deterministic responses

# Initialize the Graph Connection (The Memory/Database)
# Note: LangChain will automatically query Neo4j for its exact schema when this connects!
graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# ==========================================
# 2. THE FEW-SHOT GUARDRAILS (PROMPT ENGINEERING)
# ==========================================
# Small language models (like 3B parameter models) can hallucinate Cypher syntax.
# We inject this strict template to teach it our EXACT database schema and give it examples.
cypher_template = """
You are an expert graph database translator. 
Your job is to translate the user's natural language question into a precise Neo4j Cypher query.

Strict Rules:
1. ONLY use the nodes and relationships provided in the schema below. 
2. Do NOT hallucinate or guess any property names.
3. Your output must ONLY contain the Cypher query code. Do not explain the code. Do not add markdown blocks like ```cypher. 

Database Schema:
{schema}

Here are a few examples to guide you:

Example 1: Top expensive products
Question: What are the top 3 most expensive products?
Cypher: MATCH (p:Product) RETURN p.name, p.category, p.price ORDER BY p.price DESC LIMIT 3

Example 2: Cross-referencing orders
Question: How many products are in order ORD_0001?
Cypher: MATCH (o:Order {{id: 'ORD_0001'}})-[rel:CONTAINS]->(p:Product) RETURN count(p)

Example 3: Multi-hop traversal (Customer to Product)
Question: Which customers bought products in the Electronics category?
Cypher: MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product) WHERE p.category = 'Electronics' RETURN DISTINCT c.name

Now, translate the following question:
Question: {question}
Cypher:
"""

# Convert the string template into a LangChain Prompt Object
cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"], 
    template=cypher_template
)

# ==========================================
# 3. THE SYNTHESIS GUARDRAILS (QA PROMPT)
# ==========================================
# We must explicitly tell the SLM how to read the raw Python dictionaries.
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
    qa_prompt=qa_prompt,  # <-- The missing link to fix the synthesis failure
    allow_dangerous_requests=True 
)
# ==========================================
# 5. EXECUTION SYSTEM
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 Graph RAG Agent Online")
    print("="*50)
    
    # We test a complex "Multi-Hop" query that forces the AI to jump across 
    # Customer -> Order -> Product.
    test_question = "What is the name and price of the most expensive product bought by a customer in the Retail industry?"
    
    print(f"\nUser Question: {test_question}\n")
    print("Agent is thinking (Generating Cypher, Executing, and Synthesizing)...\n")
    
    # Run the chain
    try:
        response = qa_chain.invoke({"query": test_question})
        print("\n" + "="*50)
        print("Final Answer:")
        print(response["result"])
        print("="*50 + "\n")
    except Exception as e:
        print(f"\nPipeline Failed. Error: {e}")