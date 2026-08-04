Master Scheduler

The Master Scheduler does not run business jobs.

Its responsibility is to coordinate child schedulers.

Master Scheduler
        │
 ┌──────┼─────────┐
 │      │         │
 ▼      ▼         ▼
Auth  Business  Platform
Scheduler Scheduler Scheduler


Master Scheduler
│
├── Auth Scheduler
│      ├── OTP Cleanup
│      ├── Password Cleanup
│      └── Session Cleanup
│
├── Business Scheduler
│      ├── Loan Reminder
│      ├── Recycle Bin Cleanup
│      ├── Analytics
│      └── ...
│
├── Supplier Scheduler
│      ├── Verify Suppliers
│      ├── Expire Quotes
│      └── ...
│
├── Wallet Scheduler
│      ├── Payment Retry
│      ├── Settlement
│      └── ...
│
└── Platform Scheduler
       ├── Audit Cleanup
       ├── Backups
       └── Monitoring