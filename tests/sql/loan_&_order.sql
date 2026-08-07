-- =====================================================================
-- LOAN BOOK — data views
-- =====================================================================

-- All customers
SELECT id, name, phone, first_recorded_at, last_transaction_at, is_deleted
FROM business.loan_book_customers
ORDER BY created_at DESC;

-- All loan entries, with the customer's name joined in and amounts
-- shown in rands (the DB stores cents)
SELECT
    e.id,
    c.name                                   AS customer_name,
    (e.original_amount_cents / 100.0)        AS original_amount_rands,
    e.sale_date,
    e.description,
    e.is_settled,
    e.is_deleted
FROM business.loan_book_entries e
JOIN business.loan_book_customers c ON c.id = e.customer_id
ORDER BY e.sale_date DESC;

-- All payments, with customer name + which entry they paid against
SELECT
    p.id,
    c.name                          AS customer_name,
    (p.amount_cents / 100.0)        AS amount_rands,
    p.paid_at,
    p.loan_entry_id
FROM business.loan_book_payments p
JOIN business.loan_book_entries e ON e.id = p.loan_entry_id
JOIN business.loan_book_customers c ON c.id = e.customer_id
ORDER BY p.paid_at DESC;

-- Each customer's outstanding balance, computed live (original minus
-- payments) — a rough version of what the app shows, purely for
-- eyeballing in SQL
SELECT
    c.name,
    (COALESCE(SUM(e.original_amount_cents), 0) / 100.0)               AS total_original_rands,
    (COALESCE(SUM(p.amount_cents), 0) / 100.0)                        AS total_paid_rands,
    ((COALESCE(SUM(e.original_amount_cents), 0) - COALESCE(SUM(p.amount_cents), 0)) / 100.0) AS outstanding_rands
FROM business.loan_book_customers c
LEFT JOIN business.loan_book_entries e ON e.customer_id = c.id AND e.is_deleted = false
LEFT JOIN business.loan_book_payments p ON p.loan_entry_id = e.id
WHERE c.is_deleted = false
GROUP BY c.id, c.name
ORDER BY outstanding_rands DESC;

-- History log, most recent first
SELECT event_type, amount_cents / 100.0 AS amount_rands, reason, occurred_at
FROM business.loan_book_history_events
ORDER BY occurred_at DESC
LIMIT 50;


-- =====================================================================
-- ORDER BOOK — data views
-- =====================================================================

-- All customers
SELECT id, name, phone, is_deleted
FROM business.order_book_customers
ORDER BY created_at DESC;

-- All orders, with customer name joined in and total in rands
SELECT
    o.order_number,
    o.order_date,
    c.name                        AS customer_name,
    o.status,
    (o.total_cents / 100.0)       AS total_rands,
    o.notes,
    o.is_deleted,
    o.created_at
FROM business.order_book_orders o
JOIN business.order_book_customers c ON c.id = o.customer_id
ORDER BY o.created_at DESC;

-- Line items for every order, with the order number + customer shown
SELECT
    o.order_number,
    c.name                              AS customer_name,
    li.description,
    li.quantity,
    (li.unit_price_cents / 100.0)       AS unit_price_rands,
    (li.line_total_cents / 100.0)       AS line_total_rands
FROM business.order_book_line_items li
JOIN business.order_book_orders o ON o.id = li.order_id
JOIN business.order_book_customers c ON c.id = o.customer_id
ORDER BY o.order_number DESC;

-- Money made per day (completed orders only) — same calc the Balances
-- screen does client-side, just as raw SQL
SELECT
    DATE(completed_at)              AS day,
    COUNT(*)                        AS orders_completed,
    (SUM(total_cents) / 100.0)      AS total_rands
FROM business.order_book_orders
WHERE status = 'completed' AND is_deleted = false
GROUP BY DATE(completed_at)
ORDER BY day DESC;

-- Everything currently sitting in Trash (orders)
SELECT
    o.order_number,
    c.name                        AS customer_name,
    o.status,
    (o.total_cents / 100.0)       AS total_rands,
    o.deletion_cause,
    o.deleted_at
FROM business.order_book_orders o
JOIN business.order_book_customers c ON c.id = o.customer_id
WHERE o.is_deleted = true
ORDER BY o.deleted_at DESC;

-- Auto-clear settings per business
SELECT business_id, completed_duration, completed_custom_hours, cancelled_duration, cancelled_custom_hours
FROM business.order_book_auto_clear_settings;

-- History log, most recent first
SELECT event_type, amount_cents / 100.0 AS amount_rands, reason, occurred_at
FROM business.order_book_history_events
ORDER BY occurred_at DESC
LIMIT 50;



--- delete user

DELETE FROM auth.users WHERE email = 'owner@example.com';


-- delete user nad related dta
DO $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT id INTO v_user_id FROM auth.users WHERE email = 'owner@example.com';

    IF v_user_id IS NULL THEN
        RAISE NOTICE 'No user found with that email.';
        RETURN;
    END IF;

    -- Loan Book
    DELETE FROM business.loan_book_payments WHERE loan_entry_id IN (
        SELECT id FROM business.loan_book_entries WHERE business_id = v_user_id
    );
    DELETE FROM business.loan_book_entries WHERE business_id = v_user_id;
    DELETE FROM business.loan_book_history_events WHERE business_id = v_user_id;
    DELETE FROM business.loan_book_customers WHERE business_id = v_user_id;

    -- Order Book
    DELETE FROM business.order_book_line_items WHERE order_id IN (
        SELECT id FROM business.order_book_orders WHERE business_id = v_user_id
    );
    DELETE FROM business.order_book_orders WHERE business_id = v_user_id;
    DELETE FROM business.order_book_history_events WHERE business_id = v_user_id;
    DELETE FROM business.order_book_auto_clear_settings WHERE business_id = v_user_id;
    DELETE FROM business.order_book_customers WHERE business_id = v_user_id;

    -- auth.otp_verifications / refresh_tokens / password_reset_tokens
    -- already have ON DELETE CASCADE, so this last delete cleans those up too
    DELETE FROM auth.users WHERE id = v_user_id;

    RAISE NOTICE 'Deleted user % and all related Loan Book / Order Book data.', v_user_id;
END $$;