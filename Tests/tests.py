import pandas as pd

print("Loading orders.csv...")
orders = pd.read_csv('C:\\Users\\shrey\\Downloads\\Internship_2026\\orders.csv')

# 1. Check the raw, unfiltered count (including deleted orders)
total_posreturns = len(orders[(orders['CompanyID'] == 450) & (orders['OrderType'] == 'posreturn')])

# 2. Check the active count (IsDeleted == 0) - This is what the AI is supposed to find!
active_posreturns = len(orders[(orders['CompanyID'] == 450) & (orders['OrderType'] == 'posreturn') & (orders['IsDeleted'] == 0)])

print("\n" + "="*50)
print("📊 PANDAS GROUND TRUTH CHECK (QUESTION 8)")
print("="*50)
print(f"Total 'posreturn' for Company 450 (Including Deleted): {total_posreturns}")
print(f"Active 'posreturn' for Company 450 (IsDeleted == 0) : {active_posreturns}")
print("="*50 + "\n")