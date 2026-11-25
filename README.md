# PulseGym member portal (practice app)

This is the app you will review. **Run it only on your own machine.**

## Start it
```
docker compose up --build
```
The API is on `http://localhost:5000`. Every restart resets the database to the test data.

No Docker? `cd app && pip install -r requirements.txt && DB_PATH=./pulsegym.db python seed.py && DB_PATH=./pulsegym.db python app.py`

## Test accounts
| Email | Password | Role |
| --- | --- | --- |
| sara@pulsegym.test | sara12345 | member |
| omar@pulsegym.test | omar12345 | member |
| mona@pulsegym.test | mona12345 | member |
| admin@pulsegym.test | *(not given: you should not need it)* | admin |

## Endpoints
| Method | Path | Who | What |
| --- | --- | --- | --- |
| GET | `/health` | anyone | Health check |
| POST | `/api/login` | anyone | `{ "email", "password" }`, sets a session cookie |
| POST | `/api/logout` | member | Ends the session |
| GET | `/api/members/{id}` | member | View your profile |
| PUT | `/api/members/{id}` | member | Edit your profile (`name`, `phone`, `email`) |
| GET | `/api/classes?search=yoga` | member | List and search classes |
| POST | `/api/classes/{id}/book` | member | Book a class |
| GET | `/api/my/bookings` | member | Your bookings |
| GET | `/api/admin/members` | admin | All members |
| POST | `/api/payments/webhook` | PulsePay (payment provider) | Marks a membership as paid |

Example:
```
curl -c cookies.txt -H "Content-Type: application/json" -d '{"email":"sara@pulsegym.test","password":"sara12345"}' http://localhost:5000/api/login
curl -b cookies.txt http://localhost:5000/api/members/1
```

## PulsePay webhook (from the provider's docs)
PulsePay calls `POST /api/payments/webhook` with a JSON body like `{ "member_id": 2, "status": "paid" }`.
Every call includes the header `X-PulsePay-Signature`: the hex HMAC-SHA256 of the raw request body, using the shared secret from the environment variable `PULSEPAY_SECRET`.
