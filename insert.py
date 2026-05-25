from pymongo import MongoClient
from datetime import datetime, timedelta
import random

# ================================================================
# CONNECT TO MONGODB
# ================================================================

client = MongoClient("mongodb://localhost:27017/")
db = client["rapipay_loans"]
collection = db["loan_portfolio"]

# clear existing data
collection.drop()
print("Cleared existing data...")

# ================================================================
# MOCK DATA CONFIG
# ================================================================

nbfc_names = [
    "Ugro Capital",
    "Lendingkart",
    "Indifi Technologies",
    "FlexiLoans",
    "NeoGrowth Credit",
    "Aye Finance",
    "Kinara Capital",
    "Veritas Finance"
]

agent_names = [
    "Rajesh Kumar", "Priya Sharma", "Amit Singh",
    "Sunita Devi", "Manoj Yadav", "Kavita Patel",
    "Rohit Verma", "Anita Gupta", "Vikram Joshi",
    "Pooja Mishra", "Deepak Chauhan", "Rekha Rani",
    "Sanjay Tiwari", "Meena Kumari", "Arun Pandey"
]

employee_names = [
    "Sandeep Tiwari", "Rekha Nair",
    "Arjun Mehta", "Divya Sinha", "Karan Malhotra"
]

states = [
    "UP", "MP", "Bihar", "Rajasthan",
    "Maharashtra", "Gujarat", "Punjab", "Haryana",
    "Delhi", "Uttarakhand"
]

loan_amounts = [
    25000, 50000, 75000,
    100000, 150000, 200000,
    250000, 300000
]

# ================================================================
# GENERATE 500 LOAN RECORDS
# ================================================================

loans = []

for i in range(500):

    # dates
    disbursal_date = datetime(2024, 4, 1) + timedelta(days=random.randint(0, 365))
    tenure_months = random.choice([6, 12, 18, 24])

    # amounts
    disbursal_amount = random.choice(loan_amounts)
    interest_rate = random.choice([18, 20, 22, 24])
    emi_amount = round(disbursal_amount / tenure_months * (1 + interest_rate/100))
    total_repayable = emi_amount * tenure_months

    # overdue logic
    is_overdue = random.random() < 0.28  # 28% loans overdue
    overdue_days = random.randint(1, 180) if is_overdue else 0
    overdue_amount = round(emi_amount * random.randint(1, 4)) if is_overdue else 0

    # charges
    fldg_amount = round(disbursal_amount * 0.05)       # 5% of disbursal
    lpp_amount = round(overdue_amount * 0.02) if is_overdue else 0  # 2% of overdue

    # status
    if is_overdue:
        loan_status = "overdue"
    else:
        loan_status = random.choice(["active", "active", "active", "closed"])

    # emis
    emis_paid = random.randint(0, tenure_months - 1)
    emis_pending = tenure_months - emis_paid

    # last payment
    if emis_paid > 0 and not is_overdue:
        last_payment = disbursal_date + timedelta(days=emis_paid * 30)
    else:
        last_payment = None

    # agent and employee
    agent = random.choice(agent_names)
    employee = random.choice(employee_names)
    nbfc = random.choice(nbfc_names)
    state = random.choice(states)

    # pan generation
    pan_letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))
    pan_digits = str(random.randint(1000, 9999))
    pan_last = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    pan = pan_letters + pan_digits + pan_last

    loan = {
        "loanId":           f"LN{2024000 + i}",
        "pan":              pan,
        "merchantId":       f"MRC{random.randint(10000, 99999)}",
        "smid":             f"SM{random.randint(1000, 9999)}",
        "parentId":         f"PAR{random.randint(100, 999)}",

        "agentName":        agent,
        "agentMobile":      f"9{random.randint(100000000, 999999999)}",

        "employeeName":     employee,
        "employeeMobile":   f"8{random.randint(100000000, 999999999)}",

        "nbfcName":         nbfc,
        "state":            state,

        "disbursalDate":    disbursal_date,
        "disbursalAmount":  disbursal_amount,
        "tenureMonths":     tenure_months,
        "interestRate":     interest_rate,
        "emiAmount":        emi_amount,
        "totalRepayable":   total_repayable,

        "emisPaid":         emis_paid,
        "emisPending":      emis_pending,
        "lastPaymentDate":  last_payment,

        "overDue":          is_overdue,
        "overDueDays":      overdue_days,
        "overDueAmount":    overdue_amount,

        "fldg":             fldg_amount,
        "lpp":              lpp_amount,

        "soundBox":         random.choice([True, False]),
        "upiMandate":       random.choice(["active", "active", "inactive", "pending"]),
        "loanStatus":       loan_status,

        "createdAt":        disbursal_date,
        "updatedAt":        datetime.now()
    }

    loans.append(loan)

# ================================================================
# INSERT INTO MONGODB
# ================================================================

collection.insert_many(loans)
print(f"✅ Inserted {len(loans)} loan records")

# ================================================================
# VERIFY — PRINT SAMPLE STATS
# ================================================================

total = collection.count_documents({})
overdue = collection.count_documents({"overDue": True})
active = collection.count_documents({"loanStatus": "active"})
closed = collection.count_documents({"loanStatus": "closed"})

print(f"\n📊 Database Summary:")
print(f"   Total loans     : {total}")
print(f"   Active loans    : {active}")
print(f"   Overdue loans   : {overdue}")
print(f"   Closed loans    : {closed}")

# total disbursal
pipeline = [{"$group": {"_id": None, "total": {"$sum": "$disbursalAmount"}}}]
result = list(collection.aggregate(pipeline))
total_disbursal = result[0]["total"] if result else 0
print(f"   Total disbursed : Rs {total_disbursal:,.0f}")

# overdue amount
pipeline2 = [{"$group": {"_id": None, "total": {"$sum": "$overDueAmount"}}}]
result2 = list(collection.aggregate(pipeline2))
total_overdue = result2[0]["total"] if result2 else 0
print(f"   Total overdue   : Rs {total_overdue:,.0f}")

print(f"\n✅ Sample record:")
sample = collection.find_one({}, {"_id": 0})
for key, value in sample.items():
    print(f"   {key}: {value}")

print("\n✅ Mock data ready! Now run loan_mis_assistant.py")