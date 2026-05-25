from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import json
import os

load_dotenv()

# ================================================================
# STEP 1 — CREATE MOCK LOAN DATA IN MONGODB
# ================================================================

def create_mock_data():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["rapipay_loans"]
    collection = db["loan_portfolio"]

    # clear existing data
    collection.drop()

    nbfc_names = ["Ugro Capital", "Lendingkart", "Indifi", "FlexiLoans", "NeoGrowth"]
    agent_names = ["Rajesh Kumar", "Priya Sharma", "Amit Singh", "Sunita Devi", "Manoj Yadav",
                   "Kavita Patel", "Rohit Verma", "Anita Gupta", "Vikram Joshi", "Pooja Mishra"]
    employee_names = ["Sandeep Tiwari", "Rekha Nair", "Arjun Mehta", "Divya Sinha", "Karan Malhotra"]
    states = ["UP", "MP", "Bihar", "Rajasthan", "Maharashtra", "Gujarat", "Punjab", "Haryana"]

    loans = []
    for i in range(500):
        disbursal_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 480))
        tenure_months = random.choice([6, 12, 18, 24])
        disbursal_amount = random.choice([25000, 50000, 75000, 100000, 150000, 200000])
        emi_amount = round(disbursal_amount / tenure_months * 1.15)
        is_overdue = random.random() < 0.25
        overdue_days = random.randint(1, 180) if is_overdue else 0
        overdue_amount = round(emi_amount * random.randint(1, 4)) if is_overdue else 0
        fldg_amount = round(disbursal_amount * 0.05)
        lpp_amount = round(overdue_amount * 0.02) if is_overdue else 0
        agent = random.choice(agent_names)
        employee = random.choice(employee_names)
        nbfc = random.choice(nbfc_names)
        state = random.choice(states)

        loan = {
            "loanId": f"LN{2024000 + i}",
            "pan": f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}{random.randint(1000,9999)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=1))}",
            "merchantId": f"MRC{random.randint(10000, 99999)}",
            "smid": f"SM{random.randint(1000, 9999)}",
            "agentName": agent,
            "agentMobile": f"9{random.randint(100000000, 999999999)}",
            "employeeName": employee,
            "employeeMobile": f"8{random.randint(100000000, 999999999)}",
            "parentId": f"PAR{random.randint(100, 999)}",
            "nbfcName": nbfc,
            "state": state,
            "disbursalDate": disbursal_date,
            "disbursalAmount": disbursal_amount,
            "tenureMonths": tenure_months,
            "emiAmount": emi_amount,
            "totalRepayable": emi_amount * tenure_months,
            "overDue": is_overdue,
            "overDueDays": overdue_days,
            "overDueAmount": overdue_amount,
            "fldg": fldg_amount,
            "lpp": lpp_amount,
            "soundBox": random.choice([True, False]),
            "upiMandate": random.choice(["active", "inactive", "pending"]),
            "loanStatus": "overdue" if is_overdue else random.choice(["active", "closed", "active", "active"]),
            "emisPaid": random.randint(0, tenure_months),
            "emisPending": tenure_months - random.randint(0, tenure_months),
            "lastPaymentDate": disbursal_date + timedelta(days=random.randint(30, 300)) if not is_overdue else None,
            "createdAt": disbursal_date,
            "updatedAt": datetime.now()
        }
        loans.append(loan)

    collection.insert_many(loans)
    print(f"✅ Inserted {len(loans)} mock loan records into MongoDB")
    return collection

# ================================================================
# STEP 2 — AI CONVERTS QUESTION TO MONGODB QUERY
# ================================================================

def question_to_mongo_query(llm, question):
    schema = """
    MongoDB collection: loan_portfolio
    Fields:
    - loanId (string): unique loan ID e.g. LN2024001
    - pan (string): customer PAN number
    - merchantId (string): merchant ID
    - smid (string): sales manager ID
    - agentName (string): agent name
    - agentMobile (string): agent mobile number
    - employeeName (string): employee assigned
    - employeeMobile (string): employee mobile
    - parentId (string): parent distributor ID
    - nbfcName (string): NBFC that gave loan e.g. "Ugro Capital", "Lendingkart"
    - state (string): state e.g. "UP", "Bihar", "Maharashtra"
    - disbursalDate (date): date loan was disbursed
    - disbursalAmount (number): loan amount in rupees
    - tenureMonths (number): loan tenure in months
    - emiAmount (number): monthly EMI amount
    - totalRepayable (number): total amount to repay
    - overDue (boolean): true if loan is overdue
    - overDueDays (number): number of days overdue
    - overDueAmount (number): total overdue amount in rupees
    - fldg (number): First Loss Default Guarantee amount
    - lpp (number): Late Payment Penalty amount
    - soundBox (boolean): whether agent has soundbox
    - upiMandate (string): "active", "inactive", or "pending"
    - loanStatus (string): "active", "overdue", "closed"
    - emisPaid (number): number of EMIs paid
    - emisPending (number): number of EMIs pending
    - lastPaymentDate (date): last payment date
    - createdAt (date): record creation date
    """

    system_prompt = f"""
You are a MongoDB query generator for a loan MIS system.
Given a question in plain English, generate a valid Python dictionary representing a MongoDB aggregation pipeline or find query.

Schema:
{schema}

Rules:
1. Return ONLY a valid Python dictionary or list — no explanation, no markdown, no backticks.
2. For date filters use: datetime(YYYY, M, D) format.
3. For aggregations return a list (aggregation pipeline).
4. For simple filters return a dict (find query).
5. Current date is {datetime.now().strftime("%Y-%m-%d")}.
6. FY 2024-25 means April 1 2024 to March 31 2025.
7. Always use exact field names from schema above.

Examples:
Question: total overdue loans
Return: [{{"$match": {{"overDue": true}}}}, {{"$group": {{"_id": null, "totalOverDue": {{"$sum": "$overDueAmount"}}, "count": {{"$sum": 1}}}}}}]

Question: all loans from Ugro Capital
Return: {{"nbfcName": "Ugro Capital"}}
"""

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=question)
    ])

    return response.content.strip()

# ================================================================
# STEP 3 — RUN QUERY ON MONGODB
# ================================================================

def run_query(collection, query_str):
    try:

        query_str = query_str.replace("true", "True").replace("false", "False").replace("null", "None")
        query = eval(query_str, {"datetime": datetime})

        if isinstance(query, list):
            # aggregation pipeline
            results = list(collection.aggregate(query))
        else:
            # find query
            results = list(collection.find(query, {"_id": 0}).limit(10))

        return results
    except Exception as e:
        return f"Query error: {str(e)}"

# ================================================================
# STEP 4 — AI SUMMARIZES THE RESULT
# ================================================================

def summarize_result(llm, question, results):
    result_str = json.dumps(results, default=str, indent=2)

    response = llm.invoke([
        SystemMessage(content="You are a fintech MIS analyst. Summarize the MongoDB query result in clear business language. Be concise and highlight key numbers."),
        HumanMessage(content=f"Question: {question}\n\nData:\n{result_str}")
    ])

    return response.content

# ================================================================
# MAIN — INTERACTIVE LOAN MIS ASSISTANT
# ================================================================

def main():
    print("=" * 50)
    print("   LOAN MIS AI ASSISTANT — RapiPay")
    print("=" * 50)

    # setup
    print("\nConnecting to MongoDB...")
    collection = create_mock_data()

    print("Connecting to Groq AI...")
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )

    print("\n✅ Assistant Ready!")
    print("Type 'exit' to quit")
    print("-" * 50)
    print("Example questions:")
    print("  - Total overdue amount this FY")
    print("  - All loans from Ugro Capital")
    print("  - Agents with inactive upiMandate")
    print("  - Total disbursals in January 2025")
    print("  - Top 5 agents by loan amount")
    print("-" * 50)

    while True:
        question = input("\n Management Question: ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            continue

        print("\n Generating query...")
        query_str = question_to_mongo_query(llm, question)
        print(f" Query: {query_str}")

        print(" Running on MongoDB...")
        results = run_query(collection, query_str)

        if isinstance(results, str) and "error" in results.lower():
            print(f"❌ {results}")
            continue

        print(" Summarizing results...")
        summary = summarize_result(llm, question, results)

        print(f"\n Answer:\n{summary}")
        print("-" * 50)

if __name__ == "__main__":
    main()