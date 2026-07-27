"""Quick test for evidence items endpoint."""
import urllib.request
import json

req = urllib.request.Request(
    'http://localhost:8000/api/evidence/items?source=resume',
    headers={'X-User-Id': 'user_4a7c13b3'}
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())

print("Evidence Items Summary:")
for k, v in data.items():
    print(f"  {k}: {len(v)} items")

print("\nTop 5 Skills:")
for s in data.get('skills', [])[:5]:
    print(f"  {s['name']}: {s['confidence']:.0%}")

print("\nEndpoint OK!")
