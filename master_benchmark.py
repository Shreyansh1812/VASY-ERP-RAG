import time

# Import your GraphCypherQAChain
from rag_pipeline import cypher_chain

# ==========================================
# TEST SUITE
# ==========================================

tests = {

    "T1_IndustryDistribution": {
        "q": "What industries are represented among customers located in Texas?"
    },

    "T2_HealthcareCustomers": {
        "q": "How many customers belong to the Healthcare industry?"
    },

    "T3_FloridaCustomers": {
        "q": "How many customers are located in Florida?"
    },

    "T4_IndustryRanking": {
        "q": "List all industries and their customer counts."
    },

    "T5_TotalOrders": {
        "q": "How many orders exist in the database?"
    },

    "T6_CompletedOrders": {
        "q": "How many Completed orders exist?"
    },

    "T7_OrderStatusBreakdown": {
        "q": "Show order counts by status."
    },

    "T8_TotalRevenue": {
        "q": "What is the total revenue across all orders?"
    },

    "T9_HealthcareRevenue": {
        "q": "Calculate total revenue from Healthcare customers."
    },

    "T10_TexasRevenue": {
        "q": "Calculate total revenue from customers located in Texas."
    },

    "T11_HealthcareCompletedRevenue": {
        "q": "Calculate total revenue from Completed orders placed by Healthcare customers."
    },

    "T12_TexasCompletedRevenue": {
        "q": "Calculate total revenue from Completed orders placed by customers in Texas."
    },

    "T13_CustomersPerCompany": {
        "q": "How many customers belong to each company?"
    },

    "T14_CompanyMostOrders": {
        "q": "Which company processed the most orders?"
    },

    "T15_ProductCount": {
        "q": "How many products exist?"
    },

    "T16_MostPurchasedProducts": {
        "q": "Which products were purchased most frequently?"
    },

    "T17_ProductRevenue": {
        "q": "Which products generated the highest revenue?"
    },

    "T18_TechCompletedRevenue": {
        "q": "Calculate total revenue from Completed orders placed by Technology customers."
    },

    "T19_FinanceCompany202": {
        "q": "Calculate the revenue from products belonging to Company 202 purchased by Finance customers."
    },

    "T20_DistinctIndustries": {
        "q": "How many distinct industries exist?"
    }
}

# ==========================================
# EXECUTION
# ==========================================

print("\n" + "=" * 100)
print("STARTING GRAPH-RAG EVALUATION SUITE")
print("=" * 100)

results = []

for idx, (test_id, data) in enumerate(tests.items(), start=1):

    question = data["q"]

    print(f"\n[{idx}/{len(tests)}] {test_id}")
    print(f"QUESTION: {question}")

    start_time = time.time()

    try:

        response = cypher_chain.invoke(
            {"query": question}
        )

        runtime = round(
            time.time() - start_time,
            2
        )

        result = response.get(
            "result",
            "None"
        )

        intermediate = response.get(
            "intermediate_steps",
            []
        )

        generated_cypher = "N/A"
        db_context = "N/A"

        if len(intermediate) > 0:

            step0 = intermediate[0]

            if isinstance(step0, dict):
                generated_cypher = step0.get(
                    "query",
                    str(step0)
                )
            else:
                generated_cypher = str(step0)

        if len(intermediate) > 1:

            step1 = intermediate[1]

            if isinstance(step1, dict):
                db_context = step1.get(
                    "context",
                    str(step1)
                )
            else:
                db_context = str(step1)

        results.append({

            "Test": test_id,
            "Question": question,
            "Cypher": generated_cypher,
            "Context": db_context,
            "Result": result,
            "Runtime": runtime

        })

        print("SUCCESS")

    except Exception as e:

        runtime = round(
            time.time() - start_time,
            2
        )

        results.append({

            "Test": test_id,
            "Question": question,
            "Cypher": "FAILED",
            "Context": "FAILED",
            "Result": str(e),
            "Runtime": runtime

        })

        print(f"FAILED: {e}")

# ==========================================
# REPORT
# ==========================================

print("\n\n")
print("=" * 120)
print("FINAL GRAPH-RAG REPORT")
print("=" * 120)

for r in results:

    print("\n" + "-" * 120)

    print(f"TEST ID:")
    print(r["Test"])

    print("\nQUESTION:")
    print(r["Question"])

    print("\nGENERATED CYPHER:")
    print(r["Cypher"])

    print("\nDATABASE CONTEXT:")
    print(r["Context"])

    print("\nFINAL ANSWER:")
    print(r["Result"])

    print("\nRUNTIME:")
    print(f"{r['Runtime']} sec")

print("\n" + "=" * 120)
print(f"TOTAL TESTS EXECUTED: {len(results)}")
print("=" * 120)