# Pelangi Homestay Auth Testing

## Step 1 — MongoDB Verification
```bash
mongosh
use test_database
db.users.find({role: "admin"}).pretty()
```
Expect bcrypt hash starting with `$2b$`. Index `users.email` unique should exist.

## Step 2 — API smoke test
Use the external REACT_APP_BACKEND_URL.

```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)

# Login
curl -c /tmp/cookies.txt -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@pelangihomestay.com","password":"pelangi2026"}'

# /me
curl -b /tmp/cookies.txt "$API/api/auth/me"

# List admin posts
curl -b /tmp/cookies.txt "$API/api/admin/blog"

# Create post
curl -b /tmp/cookies.txt -X POST "$API/api/admin/blog" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","excerpt":"e","content":"c","category":"Wisata"}'

# Public
curl "$API/api/blog"

# Logout
curl -b /tmp/cookies.txt -X POST "$API/api/auth/logout"
```

Admin credentials: `admin@pelangihomestay.com` / `pelangi2026`
