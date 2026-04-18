"""Quick benchmark of API endpoints after optimisation."""
import requests
import time

BASE = "http://localhost:8000"

# Login
s = requests.Session()
passwords = ["salman"]
token = None

for pw in passwords:
    r = s.post(f"{BASE}/api/v1/auth/login/", json={"username": "salman", "password": pw})
    if r.status_code == 200:
        token = r.json()["tokens"]["access"]
        print(f"Login OK with password '{pw}'")
        break
    # Also try superuser
    r2 = s.post(f"{BASE}/api/v1/auth/login/", json={"username": "superadmin", "password": pw})
    if r2.status_code == 200:
        token = r2.json()["tokens"]["access"]
        print(f"Login OK as superadmin with password '{pw}'")
        break

if not token:
    print(f"Login failed. Last response: {r.status_code} {r.text[:300]}")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Dashboard
t0 = time.time()
r = s.get(f"{BASE}/api/v1/dashboard/", headers=headers)
dt = time.time() - t0
print(f"\nDashboard: {r.status_code} in {dt:.2f}s")
if r.status_code == 200:
    d = r.json()
    print(f"  total_assets={d['total_assets']}")
    print(f"  active={d['active_assets']}")
    print(f"  total_value={d['total_value']}")
    print(f"  total_nbv={d['total_nbv']}")
    print(f"  total_dep={d['total_depreciation']}")
    print(f"  dep_pct={d['depreciation_percentage']}%")
else:
    print(f"  Error: {r.text[:500]}")

# Dashboard (cached - 2nd call)
t0 = time.time()
r = s.get(f"{BASE}/api/v1/dashboard/", headers=headers)
dt = time.time() - t0
print(f"\nDashboard (cached): {r.status_code} in {dt:.2f}s")

# Asset List
t0 = time.time()
r = s.get(f"{BASE}/api/v1/assets/?page=1&page_size=25", headers=headers)
dt = time.time() - t0
print(f"\nAsset List: {r.status_code} in {dt:.2f}s")
if r.status_code == 200:
    d = r.json()
    print(f"  count={d['count']}, returned={len(d['results'])}")
else:
    print(f"  Error: {r.text[:500]}")

# Asset List page 2
t0 = time.time()
r = s.get(f"{BASE}/api/v1/assets/?page=2&page_size=25", headers=headers)
dt = time.time() - t0
print(f"\nAsset List p2: {r.status_code} in {dt:.2f}s")

print("\nDone!")
