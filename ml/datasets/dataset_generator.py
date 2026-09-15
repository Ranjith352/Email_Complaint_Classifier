import os
import csv
import random
from pathlib import Path

# Ensure output directory exists
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = RAW_DIR / "complaints_raw.csv"

DEPARTMENTS = {
    "Finance": {
        "categories": {
            "Billing": ["Subscription Overcharge", "Duplicate Debit", "Unexpected Fee", "Currency Conversion Error"],
            "Payments": ["Failed UPI Transaction", "Card Declined", "Gateway Timeout", "Pending Verification"],
            "Refunds": ["Late Cancellation Refund", "Partial Refund Dispute", "Refund Not Credited", "Double Charge Return"],
            "Invoices": ["Tax Invoice Missing", "Wrong GSTIN Number", "Address Correction", "Duplicate Invoice"]
        },
        "templates": [
            "I was charged twice for transaction {txn_id} on my credit card. The amount was {amount} and both debits cleared my bank account.",
            "My refund for order {order_id} of {amount} has not been credited even though customer support confirmed 7 days ago.",
            "There is an unexpected recurring billing charge of {amount} on my statement that I did not authorize.",
            "The invoice for company purchase {order_id} has the wrong corporate GSTIN number and incorrect billing address.",
            "Payment of {amount} via payment gateway timed out but money was debited from my account.",
            "I cancelled my annual plan within the 14 day guarantee period but only received a partial refund.",
            "Why am I being billed {amount} every month when I downgraded to the free tier?",
            "Unable to generate downloadable PDF tax invoices for the past quarter from the billing portal.",
            "Credit card transaction failed with error ERR_PAY_901 but amount was deducted immediately.",
            "Bank statement shows duplicate processing fee charges of {amount} for order {order_id}."
        ]
    },
    "IT": {
        "categories": {
            "Network & Connectivity": ["VPN Disconnection", "DNS Resolution Error", "Slow Bandwidth", "Firewall Block"],
            "Hardware": ["Laptop Battery Failure", "Monitor Display Glitch", "Keyboard Malfunction", "Docking Station"],
            "Software Crash": ["Application Memory Leak", "Fatal Exception On Launch", "Data Sync Failure", "Frozen Screen"],
            "Access & Permissions": ["SSO Login Loop", "MFA Token Reset", "Role Elevation Request", "Password Expiry"]
        },
        "templates": [
            "The internal portal keeps crashing with fatal error code 0x8841 whenever I submit the daily batch job.",
            "Corporate VPN keeps dropping every 10 minutes, disconnecting all active SSH sessions to production servers.",
            "My MFA token has become desynchronized and I am completely locked out of the single sign-on system.",
            "Company laptop battery is swelling and won't hold charge for more than 15 minutes off the charger.",
            "DNS resolution errors are preventing our branch office from reaching the core database cluster.",
            "Cannot access the shared department network drive after the latest OS patch was deployed.",
            "The desktop client hangs indefinitely when exporting reports larger than 50MB.",
            "SSO authentication enters an infinite redirect loop in Chrome and Edge browsers.",
            "External monitors connected through the USB-C dock randomly flicker black every few seconds.",
            "Firewall policy is blocking outgoing HTTPS requests to required partner API endpoints."
        ]
    },
    "Customer Support": {
        "categories": {
            "Account Management": ["Profile Information Update", "Email Change Request", "Account Deletion", "Verification"],
            "Onboarding": ["Setup Guide Incomplete", "API Key Provisioning", "Feature Walkthrough", "Initial Sync"],
            "Cancellation": ["Membership Termination", "Auto-Renew Disable", "Contract Review", "Service Downgrade"],
            "General Inquiry": ["Operating Hours", "Service Availability", "Documentation Query", "Feedback Submission"]
        },
        "templates": [
            "I have been trying to update my primary business email address for three days but verification emails never arrive.",
            "Please cancel my premium membership immediately and confirm that auto-renew is disabled.",
            "The onboarding documentation has broken links and outdated code examples that do not work with the latest SDK.",
            "I requested account deletion under GDPR regulations two weeks ago but my account is still active.",
            "Need guidance on how to invite additional team members and manage role-based seat allocation.",
            "Your live chat representative disconnected the session abruptly without solving my support query.",
            "I cannot complete account verification because your SMS OTP service does not support my regional carrier.",
            "Where can I find the official SLA documentation and technical specifications for enterprise tier?",
            "I want to transfer ownership of our corporate workspace to a different administrator email.",
            "No response received on my initial inquiry submitted over 96 hours ago."
        ]
    },
    "Security": {
        "categories": {
            "Unauthorized Access": ["Suspicious Login Attempt", "Unrecognized IP Address", "Session Hijack", "Compromised Token"],
            "Phishing": ["Suspicious Email Campaign", "Spoofed Domain", "Credential Harvesting", "Malicious Attachment"],
            "Data Exposure": ["Public S3 Bucket", "Sensitive Token in Logs", "PII Leakage", "API Key Exposure"],
            "Policy Violation": ["Unauthorized Tool Usage", "Data Exfiltration Risk", "Unapproved Software", "Access Sharing"]
        },
        "templates": [
            "URGENT: I received a login notification from an unrecognized IP address in Moscow while I was offline.",
            "Multiple team members received a convincing phishing email pretending to be from IT asking for SSO passwords.",
            "Our security scanner flagged an exposed API secret token in a public documentation repository.",
            "Someone attempted multiple password resets on my executive account within the past hour.",
            "Detected unauthorized export of confidential customer contact lists from our staging environment.",
            "A suspicious email with a macro-enabled macro document attachment was sent to our finance department.",
            "Session tokens do not seem to invalidate after changing my master password.",
            "Potential data exposure: diagnostic log files contain unmasked user credit card and phone numbers.",
            "Security vulnerability noticed: login endpoint does not enforce rate limiting on failed attempts.",
            "Account takeover alert: user reported unexpected password change notification and lock-out."
        ]
    },
    "Logistics": {
        "categories": {
            "Delivery Delay": ["Shipment Stuck In Transit", "Past Delivery Date", "Courier Exception", "Weather Delay"],
            "Damaged Package": ["Crushed Shipping Box", "Broken Seal", "Water Damage", "Defective Unit Inside"],
            "Missing Items": ["Incomplete Order Delivery", "Empty Box Received", "Wrong Product Shipped", "Shortage"],
            "Returns & Pickup": ["Courier Pickup Missed", "Return Label Expired", "Warehouse Receipt Delay", "Exchange"]
        },
        "templates": [
            "Tracking number {order_id} shows package in transit for 14 days with zero updates from the courier.",
            "The shipping box arrived completely crushed and the fragile electronics inside were cracked and broken.",
            "Ordered a 5-pack of commercial barcode scanners but the parcel only contained 2 units.",
            "The courier failed to show up for the scheduled return pickup window for the second consecutive time.",
            "Package was marked as delivered on the tracking portal but no package was left at our reception desk.",
            "Received completely wrong model of network switch instead of the enterprise router ordered.",
            "Return package was delivered to your warehouse 10 days ago but the exchange unit has not shipped.",
            "Delivery driver refused to deliver to the 4th floor loading bay despite enterprise delivery instructions.",
            "Urgent replacement needed: the received industrial sensors are dead on arrival.",
            "Courier tracking reports delivery exception: address unreachable even though business was open."
        ]
    }
}

SENTIMENTS = ["Negative", "Negative", "Negative", "Neutral", "Positive"]
PRIORITIES = ["P1", "P2", "P3", "P4"]

def generate_dataset(num_samples: int = 650) -> Path:
    """Generates realistic enterprise complaint records across departments and categories."""
    random.seed(42)
    records = []

    dept_names = list(DEPARTMENTS.keys())

    for i in range(num_samples):
        dept = random.choice(dept_names)
        dept_info = DEPARTMENTS[dept]

        cat_names = list(dept_info["categories"].keys())
        category = random.choice(cat_names)
        subcategories = dept_info["categories"][category]
        subcategory = random.choice(subcategories)

        template = random.choice(dept_info["templates"])

        txn_id = f"TXN{random.randint(100000, 999999)}"
        order_id = f"ORD-{random.randint(10000, 99999)}"
        amount = f"${random.randint(15, 2500)}.00"

        complaint_text = template.format(
            txn_id=txn_id,
            order_id=order_id,
            amount=amount
        )

        # Realistic Priority distribution based on department and category
        if dept == "Security" or "Unauthorized" in category or "Swelling" in complaint_text or "Swallowed" in complaint_text:
            priority = random.choice(["P1", "P1", "P2"])
            sentiment = "Negative"
        elif dept == "Finance" and ("Double" in complaint_text or "twice" in complaint_text):
            priority = random.choice(["P1", "P2", "P2"])
            sentiment = "Negative"
        elif dept == "Logistics" and "crushed" in complaint_text:
            priority = random.choice(["P2", "P3"])
            sentiment = "Negative"
        elif "General Inquiry" in category or "Operating" in subcategory:
            priority = random.choice(["P3", "P4"])
            sentiment = random.choice(["Neutral", "Positive", "Neutral"])
        else:
            priority = random.choice(PRIORITIES)
            sentiment = random.choice(SENTIMENTS)

        records.append({
            "complaint_text": complaint_text,
            "category": category,
            "department": dept,
            "subcategory": subcategory,
            "priority": priority,
            "sentiment": sentiment
        })

    # Write to CSV
    fieldnames = ["complaint_text", "category", "department", "subcategory", "priority", "sentiment"]
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} raw complaint records saved to {OUTPUT_CSV}")
    return OUTPUT_CSV

if __name__ == "__main__":
    generate_dataset()
