# Cybersecurity track: Break it, then fix it

**PulseGym** runs a small member portal: login, profiles, class booking and payment confirmations. It was built in a hurry. Your job: find its security weaknesses, prove each one safely, and fix it in the code.

## The rules of engagement (read first)
- Test **only** the copy of the app in this folder, running **on your own machine**.
- Testing any real system (Creiden's, your university's, or anyone else's) is **not allowed** and means disqualification. It is also illegal.
- Automated scanners are allowed against your local copy only.

## Start
See `README.md`: `docker compose up --build`, then the API is on `http://localhost:5000`, with three test accounts.

## What you do
For every weakness you find:
1. **Explain it:** what is wrong, and where in the code.
2. **Rate it:** Critical, High, Medium or Low, and why.
3. **Prove it safely:** exact steps or a small script that shows it on your local copy.
4. **Fix it:** change the code so the weakness is gone, **without breaking** what members and staff legitimately do.

## What you submit
- A security report: one page per finding (10 pages max), plus a one-page summary ordered by severity. Say how you used AI tools.
- Your fixed version of the app (GitHub link or zip), still starting with `docker compose up --build`.

## How you are scored (out of 100, same sheet for all tracks)
| Criteria | Points |
| --- | --- |
| Passes the hidden test | 35 |
| Quality of the approach | 25 |
| Edge cases and thinking ahead | 15 |
| Clear explanation (report) | 15 |
| Presentation (easy to run and read) | 10 |

**The hidden test:** we know every weakness planted in the app. We check how many you found, whether your severity makes sense, and we run our own tests against your fixed app: every weakness must be closed **and** every normal feature must still work. **Finding** and **fixing** are scored separately. Reporting things that aren't real problems (false alarms) costs points.

## Tips
- Read the code, not just the endpoints. Some problems are only visible in the source.
- Think like each user: a member, a stranger, the payment provider, an admin.
- A fix that breaks login is not a fix.
