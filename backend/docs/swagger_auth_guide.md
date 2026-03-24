# Testing Auth-Protected Routes in Swagger UI

## 1. Open Swagger UI

Navigate to `http://localhost:8000/docs` while the backend is running.

---

## 2. Get a Token

Expand the **Authentication** section and choose the right signup/login endpoint for the account type you want to test.

### Reviewer account
- **POST** `/auth/user/login`
- Click **Try it out → Execute**
- Request body:
  ```json
  { "email": "user@demo.com", "password": "password" }
  ```

### Owner account
- **POST** `/auth/owner/login`
- Request body:
  ```json
  { "email": "owner@demo.com", "password": "password" }
  ```

Copy the `access_token` value from the response (the long string after `"access_token": "`).

---

## 3. Authorize in Swagger UI

1. Click the **Authorize** button (🔒 padlock icon) near the top-right of the page.
2. In the **Value** field under `OAuth2PasswordBearer`, enter:
   ```
   Bearer eyJhbGci...   ← paste your full token here
   ```
   > **Important:** include the word `Bearer` and a space before the token.
3. Click **Authorize**, then **Close**.

The padlock icon turns **closed** — all subsequent requests from Swagger UI will include the `Authorization` header automatically.

---

## 4. Test a Protected Endpoint

- Expand any endpoint marked with a 🔒 icon (e.g. `GET /users/me`)
- Click **Try it out → Execute**
- The request is sent with your token; you should get a `200` response

---

## 5. Switch Between Roles

Some endpoints are **reviewer-only** (creating reviews) and some are **owner-only** (`/owner/*`).

To switch roles:
1. Click **Authorize** again
2. Click **Logout** to clear the current token
3. Log in with the other account type and paste the new token

---

## 6. Role-Specific Restrictions

| Endpoint group | Required role | Error if wrong role |
|---|---|---|
| `POST /reviews` | `user` (reviewer) | `403 Owners cannot write reviews` |
| `GET /owner/*` | `owner` | `403 Owner access required` |
| `POST /restaurants/{id}/claim` | `owner` | `403 Only restaurant owners may claim` |
| `GET /users/me`, `PUT /users/me` | either | — |
| `GET /auth/me` | either | — |

---

## 7. Testing File Uploads

Swagger UI supports multipart file uploads natively:

1. Expand e.g. `POST /users/me/photo`
2. Click **Try it out**
3. Click **Choose File** next to the `file` parameter
4. Select a JPEG/PNG/WEBP image under 5 MB
5. Click **Execute**

The response returns `{ "profile_photo_url": "/uploads/profiles/..." }`.
Prepend `http://localhost:8000` to view the image in a browser.

---

## 8. Passing Query Parameters

For `GET /restaurants`, all query params are optional:

| Param | Example | Notes |
|---|---|---|
| `q` | `pizza` | Keyword search |
| `cuisine` | `Italian` | Partial match |
| `city` | `San Francisco` | Partial match |
| `price_range` | `$$` | Exact: `$`, `$$`, `$$$`, `$$$$` |
| `rating_min` | `4.0` | Float 0–5 |
| `sort` | `rating` | `rating`, `newest`, `most_reviewed`, `price_asc`, `price_desc` |
| `page` | `1` | Starts at 1 |
| `limit` | `12` | 1–100 |

---

## 9. ReDoc (Read-Only Reference)

For a cleaner read-only view of the full API schema, open:

```
http://localhost:8000/redoc
```

ReDoc does not support Try it out but renders schemas and examples more clearly.

---

## 10. Raw OpenAPI Schema

The machine-readable OpenAPI 3.x spec is available at:

```
http://localhost:8000/openapi.json
```

Import this URL directly into Postman: **Import → Link → paste URL**.
