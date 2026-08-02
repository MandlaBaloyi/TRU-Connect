SELECT event_name, status, email, ip_address, severity, correlation_id
FROM security.audit_events ORDER BY timestamp DESC LIMIT 5;