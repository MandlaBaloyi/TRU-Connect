
******************************************************************************/

--------------------------------------------------------------------------------
-- TEST 01
-- Verify User Registration
--
-- Expected:
-- • User exists.
-- • UUID generated.
-- • Password stored as hash.
-- • Role assigned.
-- • Account active.
-- • Verification pending.
--------------------------------------------------------------------------------

SELECT
    id,
    email,
    password_hash,
    role,
    first_name,
    last_name,
    phone_number,
    account_status,
    verification_status,
    is_active,
    last_login_at,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
FROM auth.users
ORDER BY created_at DESC;

-- or
SELECT *
FROM auth.users
ORDER BY created_at DESC;



--------------------------------------------------------------------------------
-- TEST 02
-- Verify OTP Creation
--
-- Expected:
-- • OTP generated.
-- • Correct destination.
-- • Hash stored.
-- • Attempts = 0.
-- • is_used = FALSE.
--------------------------------------------------------------------------------

SELECT
    id,
    user_id,
    purpose,
    destination,
    otp_code_hash,
    attempts,
    max_attempts,
    expires_at,
    is_used,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
FROM auth.otp_verifications
ORDER BY created_at DESC;

 -- or
SELECT *
FROM auth.otp_verifications
ORDER BY created_at DESC;


--------------------------------------------------------------------------------
-- TEST 03
-- Verify Refresh Token Generation
--
-- Expected:
-- • Refresh token exists.
-- • Device ID stored.
-- • IP captured.
-- • Token not revoked.
--------------------------------------------------------------------------------

SELECT
    id,
    user_id,
    jti_hash,
    expires_at,
    revoked_at,
    device_id,
    ip_address,
    created_at,
    updated_at,
    is_deleted,
    deleted_at
FROM auth.refresh_tokens
ORDER BY created_at DESC;

-- or
SELECT *
FROM auth.refresh_tokens
ORDER BY created_at DESC;




/******************************************************************************
 BUSINESS RULE VALIDATION
******************************************************************************/

--------------------------------------------------------------------------------
-- TEST 04
-- Duplicate Email Check
--
-- Expected:
-- Zero rows.
--------------------------------------------------------------------------------

SELECT
    email,
    COUNT(*)
FROM auth.users
GROUP BY email
HAVING COUNT(*) > 1;



--------------------------------------------------------------------------------
-- TEST 05
-- Users Awaiting Verification
--------------------------------------------------------------------------------

SELECT
    email,
    verification_status,
    created_at
FROM auth.users
WHERE verification_status = 'UNVERIFIED';



--------------------------------------------------------------------------------
-- TEST 06
-- Verified Users
--------------------------------------------------------------------------------

SELECT
    email,
    verification_status,
    updated_at
FROM auth.users
WHERE verification_status = 'VERIFIED';



--------------------------------------------------------------------------------
-- TEST 07
-- Disabled Accounts
--------------------------------------------------------------------------------

SELECT *
FROM auth.users
WHERE is_active = FALSE;



--------------------------------------------------------------------------------
-- TEST 08
-- Soft Deleted Users
--------------------------------------------------------------------------------

SELECT *
FROM auth.users
WHERE is_deleted = TRUE;



--------------------------------------------------------------------------------
-- TEST 09
-- Expired OTPs
--------------------------------------------------------------------------------

SELECT *
FROM auth.otp_verifications
WHERE expires_at < NOW();



--------------------------------------------------------------------------------
-- TEST 10
-- Used OTPs
--------------------------------------------------------------------------------

SELECT *
FROM auth.otp_verifications
WHERE is_used = TRUE;



--------------------------------------------------------------------------------
-- TEST 11
-- Active OTPs
--------------------------------------------------------------------------------

SELECT *
FROM auth.otp_verifications
WHERE
    is_used = FALSE
    AND expires_at > NOW();




/******************************************************************************
 DATA INTEGRITY TESTS
******************************************************************************/

--------------------------------------------------------------------------------
-- TEST 12
-- OTP Without User
--
-- Expected:
-- Zero rows.
--------------------------------------------------------------------------------

SELECT
    o.*
FROM auth.otp_verifications o
LEFT JOIN auth.users u
ON u.id = o.user_id
WHERE u.id IS NULL;



--------------------------------------------------------------------------------
-- TEST 13
-- Refresh Token Without User
--
-- Expected:
-- Zero rows.
--------------------------------------------------------------------------------

SELECT
    r.*
FROM auth.refresh_tokens r
LEFT JOIN auth.users u
ON u.id = r.user_id
WHERE u.id IS NULL;



--------------------------------------------------------------------------------
-- TEST 14
-- User + OTP Relationship
--------------------------------------------------------------------------------

SELECT
    u.email,
    u.role,
    u.verification_status,
    o.destination,
    o.purpose,
    o.is_used,
    o.created_at
FROM auth.users u
LEFT JOIN auth.otp_verifications o
ON u.id = o.user_id
ORDER BY o.created_at DESC;



--------------------------------------------------------------------------------
-- TEST 15
-- User + Refresh Token Relationship
--------------------------------------------------------------------------------

SELECT
    u.email,
    r.device_id,
    r.ip_address,
    r.created_at
FROM auth.users u
LEFT JOIN auth.refresh_tokens r
ON u.id = r.user_id;


/******************************************************************************
 PLATFORM HEALTH
******************************************************************************/

--------------------------------------------------------------------------------
-- TEST 16
-- Total Users
--------------------------------------------------------------------------------

SELECT COUNT(*) AS total_users
FROM auth.users;



--------------------------------------------------------------------------------
-- TEST 17
-- Total OTP Records
--------------------------------------------------------------------------------

SELECT COUNT(*) AS total_otps
FROM auth.otp_verifications;



--------------------------------------------------------------------------------
-- TEST 18
-- Total Refresh Tokens
--------------------------------------------------------------------------------

SELECT COUNT(*) AS refresh_tokens
FROM auth.refresh_tokens;



--------------------------------------------------------------------------------
-- TEST 19
-- Verification Status Distribution
--------------------------------------------------------------------------------

SELECT
    verification_status,
    COUNT(*)
FROM auth.users
GROUP BY verification_status;



--------------------------------------------------------------------------------
-- TEST 20
-- User Roles
--------------------------------------------------------------------------------

SELECT
    role,
    COUNT(*)
FROM auth.users
GROUP BY role;



--------------------------------------------------------------------------------
-- TEST 21
-- Account Status
--------------------------------------------------------------------------------

SELECT
    account_status,
    COUNT(*)
FROM auth.users
GROUP BY account_status;


/******************************************************************************
 DEVELOPMENT RESET

 WARNING:
 Deletes ALL authentication data.

 DEVELOPMENT ONLY.
******************************************************************************/

TRUNCATE TABLE
    auth.otp_verifications,
    auth.refresh_tokens,
    auth.password_reset_tokens,
    auth.users
RESTART IDENTITY CASCADE;