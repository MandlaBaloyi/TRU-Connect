# Future work — tracked, not urgent

Items intentionally deferred, with the reasoning for *why* they were
deferred, so nobody has to rediscover the tradeoff later.

---

## 1. Partition `security.audit_events` by month

**Trigger to act:** once the table approaches ~10–50 million rows, or
query latency on the admin control center's date-filtered views starts
noticeably degrading — whichever comes first. Don't build this
speculatively; the complexity isn't worth it at current volume.

**Why it'll be needed eventually:** an append-only table with no upper
bound will keep growing. Query speed (not storage) is what degrades —
an index on a 2-billion-row table becomes expensive to scan AND expensive
to maintain on every INSERT. Time-based partitioning (Postgres native
declarative partitioning on the `timestamp` column) keeps date-filtered
queries fast permanently, since Postgres only scans the relevant
partition(s) instead of the whole table.

**Why it interacts with the append-only trigger:** the trigger blocks
`DELETE`, which is correct for compliance — so a future retention policy
can't just delete old rows. Retention has to be **partition detachment**
(archive a whole month as one atomic operation), not row-level deletion.
Partitioning and the append-only trigger are designed to complement each
other for this reason.

**What the actual work looks like when the time comes:**
- Migration converting the existing table to partitioned form (Postgres
  supports this without downtime, via a parallel partitioned table + data
  copy + atomic rename swap — not an in-place ALTER).
- A scheduled job (via the existing `platform/schedulers/registry.py`
  pattern already built) that auto-creates next month's partition ahead
  of time, so writes never fail from a missing partition.
- A decision on retention window and where detached/archived partitions
  go (cold storage vs. just excluded from routine queries).

---

## 2. Mobile OS/device detail is missing from audit events

**Current state:** `operating_system`, and by extension richer device
context, comes back `[null]` for every mobile (Expo/React Native) request.
`browser` correctly shows `"Mobile App"` and `platform` correctly shows
`"mobile"` — those two already have a working fallback.

**Root cause — confirmed, not a bug:** OkHttp (the underlying Android
HTTP client React Native uses) sends a bare `okhttp/4.x.x` User-Agent by
default, with no OS/device info included. This is OkHttp's own default
behavior, not something Expo specifically strips out, and not something
the backend can recover after the fact — the information was never sent.

**The real fix (mobile-app side, not backend):** add a custom header on
outgoing requests using React Native's `Platform` module, e.g.:

```typescript
// frontend/mobile/src/services/api/apiClient.ts
import { Platform } from 'react-native';

headers: {
  'X-Device-OS': `${Platform.OS} ${Platform.Version}`,
}
```

Backend side then needs one small addition: a
`get_device_os()`-equivalent getter in `shared/audit_context.py` reading
that header directly, wired into `shared/audit.py`'s enrichment step —
same pattern as the existing `X-Device-ID` header support.

**Why deferred:** requires a mobile-app change I don't have visibility
into (`apiClient.ts` wasn't provided), and the current fallback
(`platform: "mobile"`) is already enough to filter/segment mobile traffic
in the admin panel. Real OS breakdown is a nice-to-have for now, not
blocking anything.

---

## 3. Minor audit-field gaps (low priority, noted for completeness)

- **`http_status_code`** is always null — audit events publish from
  inside the service layer, before Flask has decided the final HTTP
  response code. `status: success/failure` already captures the
  functional outcome, which is what investigations actually need; this
  is likely not worth chasing unless a specific need for the numeric
  code comes up.
- **`user_id` on `login_failed` rows** is always null, even when the
  account genuinely exists (wrong-password case) — `log_login_failed()`'s
  signature never accepted a `user_id` parameter. `email` is already the
  reliable correlating field for investigations, so this is a minor gap,
  not a blocking one. Would need a small signature change to thread the
  resolved user's id through when `auth_service.py` already has it.
- **OTP resend vs. first-send** are not distinguished — `request_otp()`
  always logs `OTP_CREATED`, never `OTP_RESENT`, because the service
  function has no way to know caller intent from inside itself. If this
  distinction matters later, the fix belongs at the route layer (whichever
  endpoint specifically handles a "resend" button), not inside the shared
  service function.
- **`RefreshTokenRepository.revoke_all_for_user()`'s return value** is
  unconfirmed — `logout()`'s all-devices branch defensively treats a
  `None` return as `0` in the audit metadata. If that method doesn't
  actually return a count today, the true revoked-device count won't show
  up in `logout_all_devices` events until the repository method is
  confirmed/adjusted to return one.
