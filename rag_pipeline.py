import os
from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

# ==========================================
# 1. DATABASE CONNECTION & 2. REFRESH SCHEMA
# ==========================================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "Shreyu_12"

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD
)

# Ensure schema is up to date
graph.refresh_schema()

# ==========================================
# 3. STRICT CYPHER GENERATION PROMPT
# ==========================================
CYPHER_GENERATION_TEMPLATE = """
Task:
Generate a valid Cypher query for Neo4j.

Return ONLY Cypher.

====================================================
STRICT GRAPH SCHEMA
====================================================

{schema}

====================================================
RELATIONSHIP PATHS
====================================================

(:Customer)-[:PLACED]->(:Order)

(:Customer)-[:BELONGS_TO]->(:Company)

(:Order)-[:PROCESSED_BY]->(:Company)

(:Order)-[:HAS_LINE_ITEM]->(:OrderItem)

(:OrderItem)-[:IS_PRODUCT]->(:Product)

(:Product)-[:BELONGS_TO]->(:Company)

====================================================
PROPERTY REFERENCE
====================================================

Customer:
- id
- Name
- Industry
- Region

Order:
- id
- Status

OrderItem:
- id
- Quantity
- LineTotal
- ProductVarientID

Product:
- ProductID
- ProductName

Company:
- companyId

====================================================
ABSOLUTE RULES
====================================================

1. Use ONLY properties above.

2. Never invent properties.

3. Never invent labels.

4. Never invent relationships.

5. Revenue ALWAYS means:

SUM(toFloat(oi.LineTotal))

6. Product purchase frequency ALWAYS means:

SUM(oi.Quantity)

7. Industry ALWAYS means:

c.Industry

8. Region ALWAYS means:

c.Region

9. Company means:

co.companyId

10. Distinct count questions MUST use:

COUNT(DISTINCT ...)

11. Always use:

toLower(property) CONTAINS 'value'

for string filtering.

12. Never use SQL syntax.

13. Never use IN (...) SQL style logic.

14. Never create Cartesian products.

15. Every MATCH must remain connected.

====================================================
QUESTION → QUERY MAPPINGS
====================================================

If question asks:

"total revenue"

Use:

MATCH (c:Customer)-[:PLACED]->(o:Order)
      -[:HAS_LINE_ITEM]->(oi:OrderItem)

RETURN SUM(toFloat(oi.LineTotal))

----------------------------------------------------

If question asks:

"completed order revenue"

Use:

MATCH (c:Customer)-[:PLACED]->(o:Order)
      -[:HAS_LINE_ITEM]->(oi:OrderItem)

WHERE toLower(o.Status) CONTAINS 'completed'

RETURN SUM(toFloat(oi.LineTotal))

----------------------------------------------------

If question asks:

"industry distribution"

Use:

MATCH (c:Customer)

RETURN
c.Industry,
COUNT(*) AS CustomerCount

ORDER BY CustomerCount DESC

----------------------------------------------------

If question asks:

"customers per company"

Use:

MATCH (c:Customer)-[:BELONGS_TO]->(co:Company)

RETURN
co.companyId,
COUNT(c)

----------------------------------------------------

If question asks:

"company with most orders"

Use:

MATCH (o:Order)-[:PROCESSED_BY]->(co:Company)

RETURN
co.companyId,
COUNT(o) AS OrderCount

ORDER BY OrderCount DESC

----------------------------------------------------

If question asks:

"product revenue"

Use:

MATCH (o:Order)-[:HAS_LINE_ITEM]->(oi:OrderItem)
      -[:IS_PRODUCT]->(p:Product)

RETURN
p.ProductName,
SUM(toFloat(oi.LineTotal)) AS Revenue

ORDER BY Revenue DESC

----------------------------------------------------

If question asks:

"most purchased products"

Use:

MATCH (o:Order)-[:HAS_LINE_ITEM]->(oi:OrderItem)
      -[:IS_PRODUCT]->(p:Product)

RETURN
p.ProductName,
SUM(oi.Quantity) AS UnitsSold

ORDER BY UnitsSold DESC

----------------------------------------------------

If question asks:

"distinct industries"

Use:

MATCH (c:Customer)

RETURN COUNT(DISTINCT c.Industry)

====================================================
NEGATIVE EXAMPLES
====================================================

WRONG:

MATCH (co:Company)
RETURN co.Industry

Reason:
Company has no Industry property.

----------------------------------------------------

WRONG:

MATCH (o:Order)
RETURN SUM(o.LineTotal)

Reason:
LineTotal exists only on OrderItem.

----------------------------------------------------

WRONG:

MATCH (c:Customer)
MATCH (o:Order)

Reason:
Creates Cartesian Product.

====================================================
FEW SHOT EXAMPLES
====================================================

Question:
How many customers belong to Healthcare industry?

Cypher:

MATCH (c:Customer)
WHERE toLower(c.Industry) CONTAINS 'healthcare'
RETURN COUNT(c) AS CustomerCount

----------------------------------------------------

Question:
Calculate revenue from Healthcare customers.

Cypher:

MATCH (c:Customer)-[:PLACED]->(o:Order)
      -[:HAS_LINE_ITEM]->(oi:OrderItem)

WHERE toLower(c.Industry) CONTAINS 'healthcare'

RETURN SUM(toFloat(oi.LineTotal)) AS TotalRevenue

----------------------------------------------------

Question:
What industries are represented among customers located in Texas?

Cypher:

MATCH (c:Customer)

WHERE toLower(c.Region) CONTAINS 'texas'

RETURN
c.Industry AS Industry,
COUNT(*) AS CustomerCount

ORDER BY CustomerCount DESC

====================================================
USER QUESTION
====================================================

{question}

Cypher:
"""

# ==========================================
# 4. CYPHER PROMPT OBJECT
# ==========================================

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

# ==========================================
# 5. QA PROMPT
# ==========================================

QA_TEMPLATE = """
You are a database answering assistant.

You MUST answer ONLY using the database context.

RULES

1. Never invent information.

2. If context is empty:

None

3. If context contains one numeric result:

Return only the number.

Example:

100455293.78

4. If context contains grouped rows:

Summarize all rows.

Example:

Finance: 34
Retail: 31
Technology: 21

5. If context contains company rankings:

Return ranked list.

6. If context contains product rankings:

Return ranked list.

7. If context contains industry distribution:

Return industry names with counts.

8. Never say:
"I don't know"
or
"The context does not contain..."

Use only the context.

====================================================

Database Context:

{context}

====================================================

User Question:

{question}

====================================================

Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_TEMPLATE
)

# ==========================================
# 5. LLM INITIALIZATION
# ==========================================

# Text-to-Cypher Model (Temporarily swapped to evaluate engine competence)
# ==========================================
# 5. LLM INITIALIZATION
# ==========================================

# Text-to-Cypher Model (The Specialist Returns)
cypher_llm = ChatOllama(
    model="tomasonjo/llama3-text2cypher-demo",
    temperature=0.0
)

# QA Model
qa_llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0.0
)

# ==========================================
# 6. CHAIN CREATION
# ==========================================
cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=cypher_llm,
    qa_llm=qa_llm,
    graph=graph,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,
    verbose=True,
    return_direct=False,   # <--- Use QA LLM to format final answer
    return_intermediate_steps=True,
    allow_dangerous_requests=True
)
# ==========================================
# 7. DEBUG: TEST MODEL DIRECTLY
# ==========================================

test_prompt = cypher_prompt.format(
    schema=graph.schema,
    question="What industries are represented among customers located in Texas?"
)

print("\n" + "=" * 100)
print("PROMPT SENT TO MODEL")
print("=" * 100)
print(test_prompt)

print("\n" + "=" * 100)
print("MODEL GENERATED CYPHER")
print("=" * 100)

debug_response = cypher_llm.invoke(test_prompt)

print(debug_response.content)

print("=" * 100)

# ==========================================
# 8. INTERACTIVE CLI
# ==========================================
if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("Graph RAG Chatbot Initialized")
    print("Type your questions below.")
    print("Type 'schema' to inspect the schema.")
    print("Type 'exit' or 'quit' to close.")
    print("=" * 60)

    while True:

        user_query = input("\nAsk your Graph Database a question: ").strip()

        if user_query.lower() in ["exit", "quit"]:
            print("Closing the Graph RAG pipeline. Goodbye!")
            break

        if not user_query:
            print("Please enter a valid question.")
            continue

        # Schema Debug Command
        if user_query.lower() == "schema":

            graph.refresh_schema()

            print("\n" + "=" * 100)
            print("LIVE GRAPH SCHEMA")
            print("=" * 100)
            print(graph.schema)
            print("=" * 100 + "\n")

            continue

        try:

            print("\nQUESTION:", user_query)

            response = cypher_chain.invoke(
                {"query": user_query}
            )

            print("\n" + "-" * 60)

            intermediate = response.get("intermediate_steps")

            if intermediate and isinstance(intermediate, list):

                cypher_step = (
                    intermediate[0]
                    if len(intermediate) > 0
                    else "N/A"
                )

                context_step = (
                    intermediate[1]
                    if len(intermediate) > 1
                    else "N/A"
                )

                if isinstance(cypher_step, dict):
                    cypher_step = cypher_step.get(
                        "query",
                        cypher_step
                    )

                if isinstance(context_step, dict):
                    context_step = context_step.get(
                        "context",
                        context_step
                    )

                print("🛠️ Generated Cypher:")
                print(cypher_step)

                print("\n📦 Database Context:")
                print(context_step)

            else:
                print("No intermediate steps returned.")

            print("-" * 60)

            final_answer = response.get(
                "result",
                "None"
            )

            print(f"🤖 Answer: {final_answer}")

        except Exception as e:
            print(f"❌ Error executing pipeline: {e}")