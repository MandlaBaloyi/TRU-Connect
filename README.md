TRU CONNECT — BUSINESS APP
NAVIGATION + TOP BAR UX/UI PLAN
UPDATED AFTER REVIEW OF CURRENT IMPLEMENTATION
================================================

CORE UX PRINCIPLE
-----------------

The top bar and bottom navigation must remain CONSISTENT across both
Business and Supplier roles.

The FEATURES inside each tab can differ by role, but the navigation
architecture, visual language, spacing, icon treatment and interaction
patterns should feel like the same TRU Connect product.

BUSINESS ROLE IS THE CURRENT PRIORITY.

The current implemented business features are:

1. Loan Book
2. Order Book
3. My Business / Business Profile

These existing features should now influence the navigation architecture
instead of designing the navigation independently from the actual product.


================================================
BOTTOM NAVIGATION
================================================

The bottom navigation contains 5 permanent tabs:

1. Home
2. Account
3. Community
4. Discovery
5. More

These tabs remain in the same order and position.

The active tab uses the existing selected-state styling.

Do NOT redesign the current icons unnecessarily.

The current icons are already good.


================================================
1. HOME TAB
================================================

TOP BAR:

┌─────────────────────────────────────┐
│ TruConnect                    🔔  ⋮ │
└─────────────────────────────────────┘

LEFT:

TruConnect logo / wordmark

RIGHT:

🔔 Notifications
⋮ More/actions menu

IMPORTANT:

HOME IS INTENTIONALLY EMPTY FOR NOW.

Do NOT force features into Home simply because there is available space.

Home will be designed later after the core business experience is
established.

Eventually Home should become the main DAILY BUSINESS OVERVIEW.

Potential future Home content:

- Today's activity
- Orders requiring attention
- Customers who owe money
- Upcoming deliveries
- Restock reminders
- Important notifications
- Quick actions
- Business activity summary
- Relevant supplier activity
- Important TRU Connect updates

However, NONE of these should be forced into Home yet.

CURRENT STATE:

HOME = PLACEHOLDER / EMPTY STATE


================================================
2. ACCOUNT TAB
================================================

TOP BAR:

Account

SUBTITLE:

Your business tools


PURPOSE:

ACCOUNT IS THE BUSINESS OPERATIONS AREA.

This is where the business owner goes to access the tools they use to
RUN and MANAGE their business.

The Account tab is NOT primarily for personal account settings.

CURRENT IMPLEMENTED BUSINESS TOOLS:

--------------------------------
Loan Book
--------------------------------

Purpose:

Track money owed to the business by customers.

Core functions include:

- Record sale
- Customer balances
- Unpaid balances
- Overdue balances
- Paid balances
- Customer history
- Payments
- Trash / retention
- Loan Book history
- Balance information
- Performance information


--------------------------------
Order Book
--------------------------------

Purpose:

Track orders taken from customers.

Core functions include:

- New order
- Pending orders
- Completed orders
- Cancelled orders
- Search orders
- Order history
- Trash
- Balances
- Order performance
- Completed order tracking


IMPORTANT:

Loan Book and Order Book are TWO SEPARATE BUSINESS TOOLS.

They should remain independently accessible.

Do NOT merge them into one feature.

They solve different business problems:

Loan Book
=
"MONEY CUSTOMERS OWE ME"

Order Book
=
"ORDERS CUSTOMERS HAVE PLACED"


FUTURE BUSINESS TOOLS:

The Account tab may eventually contain approximately 5–7 business tools.

Potential future tools could include:

- Cash Counter
- Quick Receipt
- Restock Reminder
- Money Due Today
- Daily Snapshot
- Fast Queue
- Supplier Orders

However:

DO NOT ADD FEATURES JUST TO REACH 5–7.

Only add a tool when it provides a clear business function.


ACCOUNT TAB DESIGN PRINCIPLE:

ACCOUNT = BUSINESS TOOLS

NOT:

- Personal settings
- Legal information
- App information
- Help
- Privacy
- Terms
- Sign out


================================================
3. COMMUNITY TAB
================================================

TOP BAR:

Community                              🔔

Below:

[ For You ] [ Following ]


PURPOSE:

COMMUNITY = BUSINESS NETWORKING + RELATIONSHIPS + RELEVANT ACTIVITY


TRU Connect should NOT become a TikTok-style infinite scrolling feed.

Business owners are busy.

They should be able to open Community and immediately understand:

"What is relevant to my business?"


IMPORTANT BUSINESS CONTEXT:

Many businesses already have existing supplier relationships.

For example:

Business
    ↓
Existing Supplier
    ↓
Regular Stock Purchases


TRU Connect should strengthen those relationships rather than forcing
business owners to endlessly browse for suppliers.

COMMUNITY SHOULD HELP WITH:

- Existing supplier activity
- Supplier announcements
- New products from followed suppliers
- Product availability
- Restock opportunities
- Delivery updates
- Supplier updates
- Business-to-business activity
- Trusted recommendations
- Following suppliers
- Following relevant businesses
- Community announcements


IMPORTANT:

Community should make it EASY to interact with existing suppliers.

Potential future actions:

- View supplier
- View products
- Request restock
- Reorder
- Contact supplier
- View delivery update
- Follow supplier

The experience should be:

SHORT
RELEVANT
BUSINESS-FOCUSED
LOW-FRICTION

Community should NOT require excessive scrolling.


================================================
4. DISCOVERY TAB
================================================

TOP BAR:

Discovery                              🔍

Below:

[ All ] [ Learn ] [ Updates ] [ Opportunities ]


PURPOSE:

DISCOVERY = INFORMATION + EDUCATION + OPPORTUNITIES


Discovery is different from Community.

Community focuses on:

RELATIONSHIPS

Discovery focuses on:

KNOWLEDGE + INFORMATION + OPPORTUNITIES


CONTENT STRUCTURE:

Featured

How to manage your business
cash flow

[Read more]


TRU Connect Updates

New supplier network update


Business Education

Understanding business credit


CATEGORIES:

ALL
Everything relevant to the business.

LEARN
Business education and practical knowledge.

UPDATES
TRU Connect product/platform updates.

OPPORTUNITIES
Relevant opportunities for businesses.


IMPORTANT:

Discovery should be CURATED.

Do NOT build an infinite content feed.

The business owner should be able to open Discovery,
find something useful and leave.


================================================
5. MORE TAB
================================================

TOP BAR:

More


PURPOSE:

MORE = ACCOUNT MANAGEMENT + APP SETTINGS + SUPPORT


This is NOT another business dashboard.

This is NOT where daily business tools live.

This is where the user manages themselves, their business profile,
security and application settings.


CURRENT STRUCTURE:

--------------------------------
My Account
--------------------------------

Manage your personal information


--------------------------------
My Business
--------------------------------

Manage your business information


--------------------------------
Account Security
--------------------------------

Protect your account and security


--------------------------------
Settings
--------------------------------

Manage your app preferences


Then:

Version 1.0.0

Sign out


IMPORTANT CHANGE:

My Business belongs in MORE, not inside the Account business-tools area.

The current My Business / Business Profile feature should therefore
remain accessible through:

More
    ↓
My Business
    ↓
Business Profile


This keeps business OPERATIONS separate from business PROFILE MANAGEMENT.


MORE FUTURE ADDITIONS:

Only add items that genuinely belong here.

Possible future items:

- Help & Support
- Contact TRU Connect
- Report a Problem
- Privacy
- Terms & Conditions
- About TRU Connect
- App Information
- Language
- Notification Preferences
- Data / Storage Management


Do NOT add all of these automatically.

More should remain clean.


================================================
GLOBAL TOP-BAR PRINCIPLE
================================================

The old approach was:

Every tab:

TruConnect                         🔔 ⋮


THIS SHOULD NOT BE USED.

Each major tab should have a CONTEXTUAL top bar.


HOME:

TruConnect                         🔔 ⋮


ACCOUNT:

Account

Your business tools


COMMUNITY:

Community                         🔔

[ For You ] [ Following ]


DISCOVERY:

Discovery                         🔍

[ All ] [ Learn ] [ Updates ] [ Opportunities ]


MORE:

More


The top bar should answer:

"WHERE AM I?"


The bottom navigation answers:

"WHERE CAN I GO?"


The content answers:

"WHAT CAN I DO HERE?"


================================================
FEATURE SCREEN TOP BARS
================================================

Feature screens should NOT use the main navigation top bar.

When entering a feature such as Loan Book or Order Book,
use a contextual feature header.

Example:

←  Loan Book


Example:

←  Order Book


Example:

←  My Business


This creates a clear hierarchy:

MAIN TAB
    ↓
BUSINESS TOOL
    ↓
FEATURE SCREEN


For example:

Account
    ↓
Loan Book
    ↓
Customer
    ↓
Customer Details
    ↓
Payment History


Likewise:

Account
    ↓
Order Book
    ↓
Order
    ↓
Order Details


And:

More
    ↓
My Business
    ↓
Business Profile


================================================
BUSINESS TOOL HIERARCHY
================================================

ACCOUNT

Your business tools

    ├── Loan Book
    │
    ├── Order Book
    │
    └── Future business tools


MORE

Account management

    ├── My Account
    ├── My Business
    ├── Account Security
    └── Settings


This separation is VERY IMPORTANT.


================================================
LOAN BOOK UX PRINCIPLE
================================================

Loan Book should communicate one thing immediately:

"MONEY CUSTOMERS OWE ME"


The current summary:

Money owed to you
R 6 370.00
9 customers owe you

is strong because the purpose is immediately understandable.

Primary action:

Record sale


Secondary actions:

- Find customer
- View balances
- History
- Trash


Loan Book should remain focused on customer debt management.


================================================
ORDER BOOK UX PRINCIPLE
================================================

Order Book should communicate:

"ORDERS CUSTOMERS HAVE PLACED"


The current primary actions are appropriate:

New order
View balances


The order states:

All
Pending
Completed
Cancelled


are clear and useful.


Primary action:

New order


Secondary actions:

- Search orders
- View balances
- History
- Trash


Order Book should remain focused on order tracking.


================================================
MY BUSINESS UX PRINCIPLE
================================================

My Business is NOT a daily business tool.

It is the BUSINESS PROFILE / BUSINESS IDENTITY MANAGEMENT area.


Current sections include:

- Business details
- Location
- Trading details
- Contact
- Business
- Verification


The existing profile completion indicator is useful:

Business profile
92% complete


This gives the owner a clear reason to complete missing information.


My Business should eventually become the central place for:

- Business information
- Location
- Trading details
- Business verification
- Business identity
- Business profile completeness


It should NOT become a general business dashboard.


================================================
GLOBAL UX RULE
================================================

TOP BAR
=
CONTEXT


BOTTOM BAR
=
NAVIGATION


CONTENT AREA
=
FUNCTION


FEATURE SCREEN HEADER
=
LOCAL CONTEXT


Therefore:

BOTTOM NAVIGATION
tells the user where they can go.

TOP BAR
tells the user which major section they are in.

CONTENT
tells the user what they can do.

BACK HEADER
tells the user which feature/screen they are currently inside.


================================================
ROLE CONSISTENCY
================================================

BUSINESS ROLE:

Same:

- Bottom navigation
- Top-bar design language
- Navigation positions
- Icon style
- Spacing
- Interaction patterns


Different:

- Business tools
- Content
- Supplier-related functionality


SUPPLIER ROLE:

Will eventually use the SAME navigation architecture.

Supplier-specific tools will appear inside the appropriate tabs.

The goal is:

Both roles should feel like TRU Connect.

NOT:

Two completely different applications.


================================================
CURRENT BUSINESS APP INFORMATION ARCHITECTURE
================================================

BOTTOM NAVIGATION

Home
│
├── Future daily business dashboard
│
│
Account
│
├── Loan Book
│   ├── Customers
│   ├── Balances
│   ├── Payments
│   ├── History
│   └── Performance
│
├── Order Book
│   ├── Orders
│   ├── Pending
│   ├── Completed
│   ├── Cancelled
│   ├── Balances
│   ├── History
│   └── Performance
│
└── Future Business Tools
│
│
Community
│
├── For You
└── Following
│
│
Discovery
│
├── All
├── Learn
├── Updates
└── Opportunities
│
│
More
│
├── My Account
├── My Business
│   └── Business Profile
├── Account Security
├── Settings
└── Support / Legal / App Information


================================================
DESIGN PHILOSOPHY
================================================

TRU Connect is NOT trying to become:

TikTok
Instagram
Facebook
Amazon


TRU Connect exists to help people RUN THEIR BUSINESS.


Therefore prioritize:

1. Speed
2. Clarity
3. Business usefulness
4. Existing relationships
5. Low cognitive load
6. Minimal unnecessary scrolling
7. Quick access to important actions
8. Simple navigation
9. Consistent UI
10. Relevant information


CORE RULE:

EVERY SCREEN SHOULD ANSWER:

"WHY WOULD A BUSY BUSINESS OWNER OPEN THIS SCREEN?"


If there is no strong answer,
the feature/content probably does not belong there.


================================================
CURRENT IMPLEMENTATION PRIORITY
================================================

PHASE 1:

Finalize the global navigation shell.

1. Bottom navigation
   - Home
   - Account
   - Community
   - Discovery
   - More

2. Contextual top bars
   - Each tab gets its own appropriate top bar.

3. Account
   - Keep Loan Book
   - Keep Order Book
   - Add future business tools only when justified.

4. More
   - Keep My Account
   - Keep My Business
   - Keep Account Security
   - Keep Settings

5. My Business
   - Keep the existing business profile implementation.
   - Improve navigation/UX where necessary.
   - Keep profile completion visible.

6. Community
   - Build structure first.
   - Prioritize existing supplier relationships.

7. Discovery
   - Build curated content structure.

8. Home
   - Leave intentionally minimal for now.
   - Return later when enough business activity exists to make Home useful.


================================================
FINAL PRINCIPLE
================================================

DO NOT BUILD FEATURES JUST TO FILL SPACE.

TRU Connect should feel:

SIMPLE
FAST
PROFESSIONAL
BUSINESS-FIRST
TRUSTED
INTENTIONAL


The interface should make a business owner think:

"I KNOW EXACTLY WHERE TO GO."

NOT:

"THERE ARE TOO MANY THINGS HERE. WHERE DO I START?"


================================================
FINAL NAVIGATION MODEL
================================================

HOME
=
"What is happening with my business?"


ACCOUNT
=
"Which business tool do I need?"


COMMUNITY
=
"What is happening in my business network?"


DISCOVERY
=
"What useful thing can I learn or discover?"


MORE
=
"How do I manage my account, business profile and app?"


THIS IS THE CORE TRU CONNECT NAVIGATION MODEL.