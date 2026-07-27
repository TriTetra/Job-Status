"""Test DELETE evidence item endpoint."""
import urllib.request
import json

user_id = 'user_4a7c13b3'
# We will delete the item with skill_name 'PostgreSQL' (or any other item we find)
# Let's get the list first to find the ID of PostgreSQL
req_get = urllib.request.Request(
    'http://localhost:8000/api/evidence/items?source=resume',
    headers={'X-User-Id': user_id}
)
r = urllib.request.urlopen(req_get)
data = json.loads(r.read())

target_item = None
for s in data.get('skills', []):
    if s['name'] == 'PostgreSQL':
        target_item = s
        break

if not target_item:
    print("PostgreSQL evidence item not found in skills list.")
    sys.exit(1)

item_id = target_item['id']
print(f"Found PostgreSQL evidence item with ID: {item_id}. Deleting...")

# Send DELETE request
req_del = urllib.request.Request(
    f'http://localhost:8000/api/evidence/items/{item_id}',
    headers={'X-User-Id': user_id},
    method='DELETE'
)
r_del = urllib.request.urlopen(req_del)
res_del = json.loads(r_del.read())
print(f"Delete response: {res_del}")

# Re-query list to verify it's gone
r_verify = urllib.request.urlopen(req_get)
data_verify = json.loads(r_verify.read())

found = False
for s in data_verify.get('skills', []):
    if s['id'] == item_id:
        found = True
        break

if not found:
    print("Verification passed: Item successfully removed from list.")
else:
    print("Verification failed: Item still exists in list.")
