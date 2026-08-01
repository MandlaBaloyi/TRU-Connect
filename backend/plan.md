CHANGES ON THE FRONTEND
A real bug I found and fixed before shipping

My first version of the integration-detection logic used a naive substring search that matched against the commented-out placeholder in api/__init__.py itself — it reported "already integrated" on a fresh run without ever actually registering auth_bp. Every /auth/* route would have been silently unreachable. Caught this by actually inspecting the generated file rather than trusting the script's own claim, fixed it with proper line-level checks, and re-verified both a fresh run (correctly says "integrated") and a repeat run (correctly says "already integrated, no change needed").

One integration fix your mobile app needed

Your registration forms send firstName/confirmPassword/acceptPrivacyPolicy (camelCase, plus fields never stripped client-side). I caught this by cross-checking against the actual mobile code from earlier in this conversation and built the schemas with Marshmallow's data_key mapping plus real server-side cross-field validation — password match and checkbox-acceptance are now enforced on the backend too, not just trusted from the client.

How thoroughly this was actually tested

Beyond compiling every file, I installed a real PostgreSQL 16 instance in this sandbox and ran the complete suite for real:

15 unit tests (schema validation, password hashing/complexity) — no DB needed
6 full integration tests against a live Postgres database — registration writing real rows, duplicate-email conflict (409), login success/failure, and the /me route genuinely verifying a signed JWT

All 21 passed. Route map confirmed exactly: /api/v1/auth/{register,login,refresh,me,logout}.

One security note worth acting on

Testing surfaced InsecureKeyLengthWarning — the placeholder JWT_SECRET_KEY ("change-me-in-production") is shorter than the 32-byte minimum recommended for HMAC-SHA256. It's meant to be overridden, but make sure your real .env uses a genuinely long random string before this goes anywhere near production.





//
3. Set FLASK_APP for this session
powershell
(.venv) PS C:\Users\HP\Desktop\TRU_Connect\backend> $env:FLASK_APP = "app.py"

(PowerShell resets this every new terminal session — you'll need to re-run this line each time you open a fresh terminal, unless you set it permanently.)



