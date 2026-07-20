#!/usr/bin/env python3
"""
================================================================================
 TRU CONNECT MOBILE APPLICATION
 Phase 1 Project Structure & Source Code Generator (v2)
 Monorepo-aware / Expo SDK 54 / Non-destructive merge mode
================================================================================

This script targets the TRU_Connect monorepo layout:

    TRU_Connect/
    |-- backend/
    |-- database/
    |-- deployment/
    |-- docs/                  <- the 10 TRU Connect spec documents go here
    |-- frontend/
    |   |-- mobile/            <- this is where the Expo app lives
    |   `-- web/
    |-- scripts/
    `-- README.md

It is designed to be run AFTER `npx create-expo-app` has already scaffolded
`frontend/mobile` (Expo SDK 54 default template), WITHOUT destroying that
scaffold. It follows three different strategies depending on the file:

  1. WRITE  - files that are entirely ours (app/ routes, all of src/**,
              docs/**). These are written/overwritten every run, since they
              are fully owned by this generator.
  2. MERGE  - shared config files that Expo's default template also creates
              (package.json, app.json, tsconfig.json, .gitignore). These are
              read, updated with only the additions TRU Connect needs, and
              written back -- your existing settings, scripts, and asset
              paths are preserved.
  3. SKIP   - anything else (.claude/, CLAUDE.md, AGENTS.md, eslint.config.js,
              package-lock.json, assets/images/*, README.md if it already
              exists). Never touched.

Additionally, the default Expo demo screens (app/(tabs)/*, app/modal.tsx)
and demo-only components/hooks/constants at the mobile project root are
left in place by default (since they don't collide with the new src/-based
architecture), but can be removed with --clean since they are superseded by
the TRU Connect screens and are no longer part of the app's navigation.

USAGE (run from the TRU_Connect root, or pass --root):

    python generate_project_structure_phase_1.py --force
    python generate_project_structure_phase_1.py --force --clean
    python generate_project_structure_phase_1.py --root /path/to/TRU_Connect --force

After running:
    cd frontend/mobile
    npm install
    npx expo install --fix   # reconciles dependency versions for SDK 54
    npx expo start
================================================================================
"""

import argparse
import json
import os
import sys


# ==============================================================================
# EMBEDDED DOCUMENTATION (Documents 00-09) -- inserted programmatically below
# ==============================================================================
# AUTO-GENERATED: embedded documentation content
DOCS: dict = {
    '00_PROJECT_VISION.txt': "================================================================================\n                            TRU CONNECT\n                          PROJECT VISION\n                          Document 00\n================================================================================\n\nParent Platform: TruePoint\nDocument Owner: Product & Engineering Leadership\nStatus: Source of Truth — Phase 1\nVersion: 1.0\n\n================================================================================\n1. PROBLEM STATEMENT\n================================================================================\n\nMillions of informal and small businesses across South Africa — spaza shops,\nsalons, restaurants, mechanics, street vendors, and small wholesalers — operate\nentirely outside of the formal financial system.\n\nThey face a recurring set of problems:\n\n1.1 Sourcing Problems\n    - Limited visibility into which suppliers are reliable, competitively\n      priced, or capable of delivering to their area.\n    - No structured way to compare suppliers beyond word of mouth.\n    - Time lost travelling to physical markets or wholesalers to place orders.\n\n1.2 Trust Problems\n    - No shared record of a supplier's reliability, delivery performance, or\n      responsiveness.\n    - No shared record of a business's own reliability as a customer.\n    - Star ratings and reviews are easily manipulated and rarely reflect real\n      commercial behaviour.\n\n1.3 Data & Financial Invisibility\n    - Informal businesses transact largely in cash and outside of any\n      recorded system.\n    - Because there is no digital trail of their commercial activity, they\n      cannot demonstrate creditworthiness to banks or lenders.\n    - Suppliers face the same problem: they cannot easily demonstrate\n      reliability or scale to potential financial or institutional partners.\n\n1.4 Supplier-Side Problems\n    - Suppliers (FMCG suppliers, regional wholesalers, beverage suppliers,\n      manufacturers, distributors, equipment and service providers) rely on\n      manual order-taking, phone calls, and informal relationships.\n    - Suppliers have no digital channel to reach new business customers or to\n      demonstrate their own track record.\n\nThe core problem is not the absence of a marketplace. It is the absence of\ntrusted, verifiable digital infrastructure connecting businesses and\nsuppliers.\n\n================================================================================\n2. VISION\n================================================================================\n\nTRU Connect will become the trusted digital infrastructure connecting\nbusinesses, suppliers, and — in time — financial institutions across South\nAfrica.\n\nTRU Connect helps businesses discover trusted suppliers, build trusted\nbusiness relationships, and quietly creates the business data needed to\nunlock future financial opportunities.\n\nEvery ordinary business activity — searching for a supplier, asking a\nquestion, placing an order, receiving a delivery — becomes a data point in a\ngrowing, trustworthy record of commercial behaviour.\n\n================================================================================\n3. MISSION\n================================================================================\n\nTo give every informal and small business in South Africa:\n\n    - A simple way to find and order from suppliers they can trust.\n    - A digital business identity that grows automatically through everyday\n      use, without requiring manual data entry or paperwork.\n    - A pathway toward financial inclusion built on real commercial evidence\n      rather than paperwork or collateral.\n\nTo give every supplier:\n\n    - A digital storefront and order channel that reaches business customers\n      directly.\n    - A reputation system based on real transaction history rather than\n      manipulable reviews.\n    - Access, over time, to trade finance and working capital based on their\n      demonstrated performance on the platform.\n\n================================================================================\n4. TARGET USERS\n================================================================================\n\n4.1 Primary Users — Businesses\n    - Spaza shops\n    - Informal traders\n    - SMEs\n    - Local retailers\n    - Salons and hair studios\n    - Restaurants\n    - Mechanics\n    - Street vendors\n    - Small wholesalers\n\n4.2 Secondary Users — Suppliers\n    - FMCG suppliers\n    - Regional wholesalers\n    - Beverage suppliers\n    - Manufacturers\n    - Distributors\n    - Equipment suppliers\n    - Service providers\n\nBoth groups interact through a single mobile application, with the\nexperience adapted to their role.\n\n================================================================================\n5. CORE PHILOSOPHY\n================================================================================\n\nTRU Connect is built on one governing idea:\n\n    Help businesses buy better, help suppliers sell more, and quietly build\n    trusted business data in the background.\n\nThis philosophy has three direct implications for product design:\n\n5.1 Invisible Data Collection\n    Users should never feel like they are filling out a credit application\n    or building a financial record. Every normal action — searching,\n    asking a question, ordering — should feel like an ordinary part of\n    running a business, while quietly contributing to a structured business\n    profile behind the scenes.\n\n5.2 Relationships Over Transactions\n    Unlike a conventional marketplace, TRU Connect optimises for durable,\n    repeat relationships between specific businesses and suppliers, not\n    one-off transactions. Repeat behaviour is the strongest trust signal\n    available and is treated as such throughout the product.\n\n5.3 Trust Before Lending\n    Financial products (credit, trade finance, working capital) are never\n    the entry point. They are the eventual output of a long period of\n    verified, trusted commercial activity. Trust must be earned and\n    observed before it can be underwritten.\n\n================================================================================\n6. WHY INFORMAL BUSINESSES\n================================================================================\n\nInformal businesses are chosen as the primary user group because:\n\n    - They represent an enormous, underserved segment of the economy with\n      real, recurring purchasing needs (stock, supplies, equipment).\n    - They are almost entirely excluded from formal credit and financial\n      services today, despite being creditworthy in practice.\n    - Their daily operational needs (finding suppliers, placing orders) are\n      immediate and valuable enough to drive habitual use, independent of\n      any future financial product.\n    - Habitual use is exactly what is required to generate the volume and\n      quality of behavioural data needed to build trusted business profiles.\n\n================================================================================\n7. WHY SUPPLIERS\n================================================================================\n\nSuppliers are included as a first-class user group, not an afterthought,\nbecause:\n\n    - A marketplace without engaged, responsive suppliers has nothing for\n      businesses to discover.\n    - Suppliers benefit directly and immediately from a digital order\n      channel and reduced manual overhead, giving them a standalone reason\n      to participate.\n    - Supplier reliability (delivery performance, responsiveness, pricing\n      consistency) is itself a critical trust signal that businesses need,\n      and that only suppliers can generate through their own activity.\n    - Over time, suppliers themselves become candidates for trade finance\n      and working capital products, mirroring the trust-building journey of\n      businesses.\n\n================================================================================\n8. WHY TRUST BEFORE LENDING\n================================================================================\n\nTRU Connect deliberately sequences its roadmap so that trust infrastructure\nis built before any financial product is introduced.\n\n    - Lending without a trust foundation is high-risk and unsustainable at\n      the scale TRU Connect intends to operate.\n    - Businesses and suppliers are more willing to engage with a tool that\n      solves an immediate operational problem (sourcing, selling) than one\n      that immediately positions itself as a financial or credit product.\n    - A trust and data layer built from real, verified commercial activity\n      produces far stronger risk signals than self-reported financial\n      information.\n    - This sequencing (utility first, trust second, credit third) is what\n      allows TRU Connect to eventually underwrite financial products with\n      confidence, rather than relying on traditional collateral or\n      documentation-heavy processes that exclude the very businesses it\n      aims to serve.\n\n================================================================================\n9. LONG-TERM VISION\n================================================================================\n\nTRU Connect is designed to evolve in four broad phases:\n\n    Phase 1 — Establish the core marketplace: supplier discovery, ordering,\n               verification, and business questions.\n    Phase 2 — Introduce payments, wallet functionality, and business\n               insights derived from platform activity.\n    Phase 3 — Introduce credit, trade finance, and working capital products,\n               underwritten using data generated in Phases 1 and 2.\n    Phase 4 — Open the platform via partner APIs to financial institutions\n               and other ecosystem partners, positioning TRU Connect as\n               shared trust infrastructure for the informal economy.\n\nOver time, TRU Connect aims to support millions of businesses and suppliers,\nbecoming the default trusted layer between informal commerce and the formal\nfinancial system in South Africa.\n\n================================================================================\n10. SUCCESS METRICS\n================================================================================\n\nSuccess for TRU Connect is measured differently at each phase, but always in\nterms of relationships and trust, not just transaction volume.\n\n10.1 Phase 1 Metrics (Engagement & Trust Foundations)\n    - Number of verified businesses and suppliers onboarded.\n    - Number of active supplier-business relationships (repeat interactions\n      between the same pair of accounts).\n    - Order completion rate and repeat order rate.\n    - Business Question engagement (questions asked, response rate, response\n      time).\n    - Supplier response rate and average response time.\n    - Month-over-month retention of both businesses and suppliers.\n\n10.2 Longer-Term Metrics (Trust & Financial Readiness)\n    - Growth in Business Health Score / Digital Business Profile completeness\n      across the user base.\n    - Percentage of businesses with sufficient verified activity to be\n      considered for future financial products.\n    - Supplier reliability scores and their correlation with business\n      retention.\n    - Volume and value of orders flowing through the platform.\n    - Eventual: credit product uptake, repayment performance, and trade\n      finance volume, once Phase 3 is reached.\n\nUltimately, TRU Connect's success is measured by the depth and reliability\nof the trusted commercial data it generates — the asset that makes every\nlater phase of the platform possible.\n",
    '01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt': '================================================================================\n                            TRU CONNECT\n                     PRODUCT SPECIFICATION\n                          Document 01 ⭐\n                    (Master Source of Truth)\n================================================================================\n\nVersion: 1.0\nRelated Documents: 00_PROJECT_VISION.txt, 09_ECOSYSTEM_STRATEGY.txt\n\n================================================================================\n1. PRODUCT PHILOSOPHY\n================================================================================\n\nTRU Connect helps businesses buy better, helps suppliers sell more, and\nquietly builds trusted business data in the background.\n\nUsers should never feel like they are completing credit applications or\ncreating financial records. Every normal business activity — searching,\nasking questions, ordering, receiving deliveries — contributes to a trusted\ndigital business profile without requiring any deliberate data-entry effort\nfrom the user.\n\nGuiding product principles (elaborated in Section 10):\n\n    - Simple First\n    - Business Focused\n    - Component Driven\n    - Mobile First\n    - Trust by Design\n    - Scalable Architecture\n\n================================================================================\n2. APPLICATION OVERVIEW\n================================================================================\n\nTRU Connect is a single React Native mobile application serving two distinct\nuser experiences from one shared codebase, backend, and database.\n\n                              TRU CONNECT\n                                   |\n                  -------------------------------------\n                  |                                     |\n          FOR BUSINESSES                        FOR SUPPLIERS\n          (Primary Users)                       (Secondary Users)\n\nBoth experiences share the following backend systems:\n\n    - Authentication\n    - Database\n    - Notifications\n    - Product Catalogue\n    - Orders\n    - Messaging / Business Questions\n    - Verification\n\nOnly the presented features and navigation differ according to the\nauthenticated user\'s role (business vs. supplier).\n\n================================================================================\n3. ONE APP, TWO EXPERIENCES\n================================================================================\n\n3.1 Role Determination\n    A single account is associated with exactly one role at a time\n    (business or supplier). Role is established at registration and\n    determines which dashboard, navigation set, and feature set the user\n    sees after authentication.\n\n3.2 Shared Infrastructure, Divergent UI\n    The application shell (authentication, notifications, settings, support)\n    is shared. Role-specific modules (dashboards, catalogues, order\n    management) are rendered conditionally based on role, using the shared\n    component library defined in Document 03.\n\n================================================================================\n4. BUSINESS USER JOURNEY\n================================================================================\n\n    Launch App\n        |\n    Landing Screen (role selection: Business / Supplier)\n        |\n    Authentication (Login / Register / Continue with Google)\n        |\n    Business Dashboard (Home)\n        |\n    Daily Operations:\n        - Browse / search suppliers\n        - View supplier profiles and products\n        - Ask Business Questions on products\n        - Bookmark / follow suppliers\n        - Place orders\n        - Track order status and delivery\n        - View and manage Digital Business Profile\n        - Manage business documents and verification\n        - Receive notifications (order updates, responses, promotions)\n\n4.1 First-Time Business Experience\n    1. View landing screen introduction slides (business-focused).\n    2. Register or continue with Google.\n    3. Complete lightweight business profile (name, category, location).\n    4. Land on Home dashboard with guided prompts (e.g. "Find your first\n       supplier").\n    5. Begin building Digital Business Profile automatically as they browse\n       and transact.\n\n================================================================================\n5. SUPPLIER USER JOURNEY\n================================================================================\n\n    Launch App\n        |\n    Landing Screen (role selection: Business / Supplier)\n        |\n    Authentication (Login / Register / Continue with Google)\n        |\n    Supplier Dashboard (Home)\n        |\n    Daily Operations:\n        - Manage product catalogue\n        - Receive and respond to orders\n        - Respond to Business Questions on products\n        - Publish Business Updates (promotions, new products, hours)\n        - View customer enquiries\n        - Track order fulfilment and delivery\n        - View business performance and statistics\n        - Manage verification and supplier documents\n\n5.1 First-Time Supplier Experience\n    1. View landing screen introduction slides (supplier-focused).\n    2. Register or continue with Google.\n    3. Complete supplier profile (business name, category, regions served).\n    4. Upload initial product catalogue.\n    5. Begin receiving business enquiries and orders; profile statistics\n       accrue automatically.\n\n================================================================================\n6. NAVIGATION\n================================================================================\n\n6.1 Business Bottom Navigation (5 tabs)\n    - Home       — daily overview and recommendations\n    - Business    — profile, verification, wallet, insights, documents\n    - Suppliers   — discovery, search, categories, saved suppliers\n    - Orders      — current, pending, completed, cancelled orders\n    - More        — settings, support, account\n\n6.2 Supplier Bottom Navigation (5 tabs)\n    - Home        — daily overview and performance\n    - Products    — catalogue management\n    - Orders      — order fulfilment and history\n    - Customers   — enquiries and customer statistics\n    - More        — settings, support, account\n\nNavigation structure is defined in detail, including component composition,\nin Document 03 (Frontend Component Specification).\n\n================================================================================\n7. FEATURES & MODULES (PHASE 1 SCOPE)\n================================================================================\n\n7.1 Authentication Module\n    - Login\n    - Register\n    - Continue with Google\n    - (Future: Phone Login, Biometric Authentication, Passkeys)\n\n7.2 Business Dashboard Module\n    - Welcome / business summary card\n    - Today\'s Orders\n    - Pending Orders\n    - Nearby Suppliers\n    - Recommended Products\n    - Recent Activity\n\n7.3 Supplier Dashboard Module\n    - Welcome / supplier summary card\n    - Today\'s Orders\n    - Customer Enquiries\n    - Recent Orders\n    - Top Products\n    - Business Performance\n\n7.4 Supplier Discovery Module (Business-facing)\n    - Search\n    - Categories\n    - Nearby Suppliers\n    - Featured Suppliers\n    - Popular Products\n    - Recently Viewed\n    - Saved Suppliers\n\n7.5 Product Catalogue Module (Supplier-facing)\n    - Product listing management\n    - Categories\n    - Pricing and bulk pricing\n    - Availability and stock status\n    - Minimum order quantities\n\n7.6 Orders Module (Shared)\n    - Order placement (business)\n    - Order acceptance / rejection (supplier)\n    - Order status tracking\n    - Invoices\n    - Delivery tracking\n    - Order history (current, pending, completed, cancelled)\n\n7.7 Business Questions Module (Shared)\n    - Ask a question beneath a product (business)\n    - Respond to a question (supplier)\n    - Questions and answers remain attached to the product for future\n      visibility (see Document 09 for rationale).\n\n7.8 Verification Module\n    - Business verification\n    - Supplier verification\n    - Verification badge display across profiles and cards\n\n7.9 Notifications Module\n    - Order status changes\n    - New responses to Business Questions\n    - Business Updates from followed/saved suppliers\n    - System and account notifications\n\n7.10 Digital Business Profile Module\n    - Automatically generated business statistics (orders, suppliers,\n      average order value, repeat supplier rate, payment behaviour,\n      business growth, risk level)\n    - See Document 07 for the underlying trust engine.\n\n7.11 Business Updates Module (Supplier-facing)\n    - Publish updates: new products, promotions, price changes, holiday\n      hours, new locations, service announcements.\n\n================================================================================\n8. SCREENS (PHASE 1)\n================================================================================\n\n8.1 Shared / Pre-Authentication Screens\n    - Landing Screen (with two-slide role introduction)\n    - Login Screen\n    - Register Screen\n    - Google Authentication flow screen\n\n8.2 Business Screens\n    - Business Home Dashboard\n    - Business Profile\n    - Verification\n    - Wallet (future-scoped placeholder in Phase 1)\n    - Saved Suppliers\n    - Business Documents\n    - Business Insights (future-scoped placeholder in Phase 1)\n    - Supplier Search / Discovery\n    - Supplier Profile (public view)\n    - Product Detail (with Business Questions thread)\n    - Cart / Order Placement\n    - Order List (current, pending, completed, cancelled)\n    - Order Detail / Delivery Tracking\n    - Notifications\n    - Settings / More\n\n8.3 Supplier Screens\n    - Supplier Home Dashboard\n    - Product Catalogue Management\n    - Product Create / Edit\n    - Order List (incoming, accepted, completed, cancelled)\n    - Order Detail / Fulfilment\n    - Customer Enquiries List\n    - Business Performance / Statistics\n    - Business Updates Composer\n    - Notifications\n    - Settings / More\n\n================================================================================\n9. USER ROLES\n================================================================================\n\n9.1 Business (Primary)\n    Permissions: search/browse suppliers, view public supplier profiles,\n    ask Business Questions, bookmark suppliers, place orders, manage own\n    business profile and documents, view own Digital Business Profile.\n\n9.2 Supplier (Secondary)\n    Permissions: manage own product catalogue, respond to Business\n    Questions, accept/reject/fulfil orders, publish Business Updates,\n    view own customer statistics (aggregated, privacy-preserving — see\n    Document 09, Business Privacy).\n\n9.3 Future Roles (Not in Phase 1 scope, noted for architecture readiness)\n    - Platform Administrator (internal moderation, verification review)\n    - Financial Partner (read-only access to aggregated trust data via\n      future partner APIs — Phase 4)\n\n================================================================================\n10. PRODUCT DESIGN PRINCIPLES\n================================================================================\n\nEvery screen and feature within TRU Connect must follow these principles:\n\n    1. Simple First — Prioritise clarity over visual complexity. Every\n       screen should answer one clear question for the user.\n    2. Business Focused — Every feature should help businesses buy, sell,\n       or grow. Features that do not serve this goal are out of scope.\n    3. Component Driven — Build reusable components (Document 03) that\n       scale consistently across both business and supplier experiences.\n    4. Mobile First — Design for fast, intuitive use on smartphones,\n       including on lower-end devices and inconsistent connectivity.\n    5. Trust by Design — Verification, transparency, and security are\n       embedded throughout the experience, not bolted on afterward.\n    6. Scalable Architecture — Every feature must support future expansion\n       into supplier services, financial products, and institutional\n       partnerships without requiring architectural rework.\n\n================================================================================\n11. FUTURE EXPANSION (ROADMAP SUMMARY)\n================================================================================\n\nSee Document 08 (Product Roadmap) for full detail. Summary:\n\n    Phase 2 — Payments, Wallet, Business Insights, Supplier Analytics\n    Phase 3 — Credit, Trade Finance, Working Capital, Financial Products\n    Phase 4 — Partner APIs, Financial Institution Integrations, Open\n              Platform Expansion\n\nArchitectural decisions in Documents 04 (Database Design) and 05 (Backend\nAPI Specification) explicitly account for this roadmap to avoid rework as\neach phase is introduced.\n',
    '02_SYSTEM_UI_UX_SPECIFICATION.txt': '================================================================================\n                            TRU CONNECT\n                    SYSTEM UI/UX SPECIFICATION\n                          Document 02\n================================================================================\n\nTarget Platform: React Native (iOS & Android)\nVersion: 1.0\nRelated Documents: 01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt,\n                    03_FRONTEND_COMPONENT_SPECIFICATION.txt\n\n================================================================================\n1. DESIGN PRINCIPLES\n================================================================================\n\n1.1 Simple First\n    Every screen should communicate its purpose within one glance. Avoid\n    decorative complexity that does not aid comprehension or action.\n\n1.2 Trust by Design\n    Verification badges, supplier statistics, and transparent business\n    information should be visually prominent, never buried in secondary\n    screens.\n\n1.3 Mobile First & Low-Bandwidth Aware\n    Layouts must remain legible and usable on small, lower-end Android\n    devices, with graceful handling of slow or intermittent connectivity\n    (skeleton loading states, cached content, optimistic UI where safe).\n\n1.4 Consistency Across Roles\n    Business and Supplier experiences should feel like the same product\n    wearing two hats — shared visual language, shared components, distinct\n    content.\n\n1.5 Accessibility First\n    Legible type sizes, adequate touch targets, sufficient colour contrast,\n    and screen-reader compatibility are baseline requirements, not\n    enhancements.\n\n================================================================================\n2. MOBILE UX GUIDELINES\n================================================================================\n\n2.1 Navigation Pattern\n    Bottom tab navigation (5 tabs) is the primary navigation pattern for\n    both roles. Stack navigation is used within each tab for drill-down\n    flows (e.g. Suppliers tab -> Supplier Profile -> Product Detail).\n\n2.2 Touch Targets\n    Minimum touch target size: 44x44 density-independent pixels (dp),\n    consistent with platform accessibility guidelines.\n\n2.3 Loading & Empty States\n    Every list-based screen must define both a Loading State and an Empty\n    State (see Document 03, Shared Components). Never present a blank\n    screen while data is pending or absent.\n\n2.4 Feedback & Confirmation\n    Destructive or high-consequence actions (cancel order, reject order,\n    delete document) require explicit confirmation via a Dialog component.\n\n2.5 Offline Tolerance\n    Core read operations (viewing cached supplier profiles, past orders)\n    should degrade gracefully offline, with a persistent but unobtrusive\n    connectivity indicator.\n\n================================================================================\n3. NAVIGATION STRUCTURE\n================================================================================\n\n3.1 Business Navigation\n    Tab bar icons and labels:\n        Home | Business | Suppliers | Orders | More\n\n3.2 Supplier Navigation\n    Tab bar icons and labels:\n        Home | Products | Orders | Customers | More\n\n3.3 Header Behaviour\n    Each top-level tab uses a persistent App Header (see Document 03)\n    showing context (page title, notification icon, profile icon). Detail\n    screens use a back-navigation header with contextual title.\n\n================================================================================\n4. TYPOGRAPHY\n================================================================================\n\nA single type scale is used across both experiences.\n\n    Display        — 28sp / Bold      — Dashboard greetings, key totals\n    Heading 1       — 22sp / Semibold  — Screen titles\n    Heading 2       — 18sp / Semibold  — Section headers, card titles\n    Body            — 15sp / Regular   — Primary content text\n    Body Small      — 13sp / Regular   — Secondary / supporting text\n    Caption         — 11sp / Medium    — Labels, timestamps, badges\n\nFont family: a single system-safe sans-serif font family should be selected\nat implementation time and applied consistently (e.g. via a shared theme\nprovider) rather than mixed across screens.\n\nLine height should be set at approximately 1.4x font size for body text to\npreserve readability on small screens.\n\n================================================================================\n5. COLOR PALETTE\n================================================================================\n\nThe palette is organised into functional roles rather than fixed hex values,\nso that theming (including future dark mode) can be layered on without\nredesign.\n\n    Primary          — Brand colour; primary actions, active tab, key CTAs\n    Primary Dark      — Pressed / active states of primary elements\n    Secondary        — Supporting brand colour; secondary actions, highlights\n    Success           — Verified status, completed orders, positive trends\n    Warning           — Pending status, low stock, attention-needed states\n    Danger            — Cancelled orders, destructive actions, errors\n    Neutral 900–100   — Text and surface greyscale range (dark to light)\n    Surface           — Card and screen background\n    Border            — Dividers, card outlines, input borders\n\nVerification badges consistently use the Success colour role; pending\nstates consistently use the Warning colour role, across both business and\nsupplier experiences, to build recognisable visual trust cues.\n\n================================================================================\n6. COMPONENTS (SUMMARY)\n================================================================================\n\nFull technical definitions live in Document 03. This document defines their\nvisual and interaction rules:\n\n    - App Header — persistent, contextual, houses notification and profile\n      access.\n    - Search Bar — persistent at top of discovery-oriented screens.\n    - Bottom Navigation — 5-tab, role-dependent.\n    - Business Card / Supplier Card / Product Card / Order Card / Customer\n      Card — consistent card shell (rounded corners, elevation, consistent\n      padding) with role-specific content.\n    - Statistics Card — used for Digital Business Profile and Supplier\n      Performance; emphasises a single metric with supporting label and\n      trend indicator.\n    - Notification Card — unread/read visual states.\n    - Verification Badge — small icon + label, Success colour role, used\n      consistently across all card types.\n    - Category Chips — horizontally scrollable, single-select or\n      multi-select depending on context.\n    - Action Button — primary, secondary, and tertiary visual variants.\n    - Empty State — icon + short message + optional call-to-action.\n    - Loading State — skeleton placeholders matching the shape of the\n      content being loaded, rather than a generic spinner, wherever\n      feasible.\n\n================================================================================\n7. CARDS\n================================================================================\n\nAll card components share:\n    - Consistent corner radius across the app (single value, defined once\n      in the shared theme).\n    - Consistent elevation/shadow treatment.\n    - Consistent internal padding and spacing rhythm (see Section 9).\n    - A predictable content hierarchy: primary identifier (name/title) at\n      top, supporting metadata in the middle, action or status indicator\n      at the bottom or trailing edge.\n\n================================================================================\n8. BUTTONS\n================================================================================\n\n    Primary Button    — Solid fill, Primary colour, used for the single\n                         most important action on a screen.\n    Secondary Button   — Outlined, Primary colour border and text, used for\n                         supporting actions.\n    Tertiary Button    — Text-only, used for low-emphasis actions (e.g.\n                         "Skip", "Not now").\n    Destructive Button — Danger colour role, used only for actions that\n                         cancel, reject, or delete.\n\nOnly one Primary Button should appear per screen or per card context to\npreserve clear visual hierarchy.\n\n================================================================================\n9. FORMS\n================================================================================\n\n    - Inputs use a consistent height, border, and focus-state treatment.\n    - Labels are always visible above the input (not placeholder-only),\n      to support usability for less digitally experienced users.\n    - Validation errors appear inline, beneath the relevant field, in the\n      Danger colour role.\n    - Multi-step forms (e.g. business registration, product creation) use\n      a visible step indicator.\n\n================================================================================\n10. ICONS\n================================================================================\n\n    - A single icon set is used throughout the application for visual\n      consistency (line-style icons recommended for clarity at small\n      sizes).\n    - Navigation icons always pair with text labels; icons are never used\n      alone for primary navigation, to support first-time and less\n      digitally experienced users.\n\n================================================================================\n11. LAYOUT & SPACING\n================================================================================\n\nA single spacing scale should be used throughout (expressed as multiples of\na base unit, e.g. 4dp):\n    xs = 4dp, sm = 8dp, md = 16dp, lg = 24dp, xl = 32dp\n\n    - Screen horizontal padding: md (16dp) as a baseline.\n    - Vertical spacing between stacked cards: sm–md (8–16dp).\n    - Section spacing (between major dashboard sections): lg (24dp).\n\n================================================================================\n12. ANIMATIONS\n================================================================================\n\nAnimations should be purposeful and brief (150–250ms for most transitions),\nsupporting comprehension rather than decoration:\n\n    - Screen transitions: standard platform-native push/pop and tab-switch\n      animations.\n    - Loading skeletons: subtle shimmer, not spinners, for card-shaped\n      content.\n    - Status changes (e.g. order accepted): brief, subtle confirmation\n      animation on the relevant card or badge.\n    - Avoid animation on data that updates frequently (e.g. statistics\n      counters) to prevent visual noise.\n\n================================================================================\n13. ACCESSIBILITY\n================================================================================\n\n    - Minimum contrast ratio of 4.5:1 for body text against its background.\n    - All interactive elements must have accessible labels for screen\n      readers (React Native accessibilityLabel).\n    - Dynamic font scaling (OS-level text size settings) must be supported\n      without breaking layout.\n    - Colour must never be the sole indicator of status (e.g. verification\n      badges pair colour with an icon and text label, not colour alone).\n',
    '03_FRONTEND_COMPONENT_SPECIFICATION.txt': '================================================================================\n                            TRU CONNECT\n                FRONTEND COMPONENT SPECIFICATION\n                          Document 03\n================================================================================\n\nTarget Platform: React Native\nVersion: 1.0\nRelated Documents: 02_SYSTEM_UI_UX_SPECIFICATION.txt\n\nPurpose: Define every reusable component in the TRU Connect React Native\ncomponent library. Every screen in the application must be composed from\nthese components rather than one-off, screen-specific implementations.\n\n================================================================================\n1. COMPONENT LIBRARY STRUCTURE\n================================================================================\n\nComponents are organised into four groups:\n\n    1. Authentication Components\n    2. Business Components\n    3. Supplier Components\n    4. Shared Components\n\nEach component below is defined by: Purpose, Props (conceptual, not code),\nVisual States, and Usage Notes.\n\n================================================================================\n2. AUTHENTICATION COMPONENTS\n================================================================================\n\n2.1 LoginScreen\n    Purpose: Capture credentials and authenticate an existing user.\n    Contains: Email/username input, password input, "Continue with Google"\n    action, "Forgot password" link, link to Register.\n    States: default, validating, error (invalid credentials), loading.\n\n2.2 RegisterScreen\n    Purpose: Create a new account and capture initial role (Business or\n    Supplier).\n    Contains: Role selector, basic account fields, terms acceptance,\n    "Continue with Google" action, link to Login.\n    States: default, validating, error, loading.\n\n2.3 GoogleAuthButton\n    Purpose: Trigger Google OAuth flow.\n    Props: onSuccess handler, onError handler, role context (business or\n    supplier, for first-time registrations).\n    States: default, loading, error.\n\n2.4 RoleSelector\n    Purpose: Let a first-time user choose Business or Supplier during\n    registration or on the landing screen.\n    Props: selectedRole, onSelect.\n    States: unselected, business-selected, supplier-selected.\n\n================================================================================\n3. BUSINESS COMPONENTS\n================================================================================\n\n3.1 BusinessSummaryCard\n    Purpose: Dashboard summary of the business\'s account (name, category,\n    verification status).\n    Props: businessName, category, verificationStatus.\n\n3.2 SupplierCard\n    Purpose: Represent a supplier in list/grid contexts (search results,\n    nearby suppliers, saved suppliers).\n    Props: supplierName, category, distance (optional), verificationStatus,\n    ratingSummary (derived from Business Questions / statistics, not star\n    rating — see Document 09), onPress.\n    States: default, saved/bookmarked, unverified.\n\n3.3 ProductCard\n    Purpose: Represent a product in catalogue, search, or recommendation\n    contexts.\n    Props: productName, price, unit, supplierName, availabilityStatus,\n    thumbnailImage, onPress.\n    States: default, out-of-stock, on-promotion.\n\n3.4 OrderCard (Business view)\n    Purpose: Represent a single order in the business\'s order list.\n    Props: orderId, supplierName, status (pending/accepted/completed/\n    cancelled), totalAmount, orderDate, onPress.\n    States: pending, accepted, completed, cancelled, delayed.\n\n3.5 CategoryCard / Category Chips\n    Purpose: Browse suppliers or products by category.\n    Props: categoryName, icon, isSelected, onPress.\n\n3.6 BusinessQuestionThread\n    Purpose: Display and submit Business Questions beneath a product.\n    Props: productId, questions (list of question + supplier response +\n    timestamp), onSubmitQuestion.\n    States: no questions yet (empty state), questions with pending\n    response, questions with response.\n\n3.7 DigitalBusinessProfileCard\n    Purpose: Present the automatically generated business trust profile\n    (see Document 07).\n    Props: businessSince, ordersCount, suppliersCount, averageOrderValue,\n    repeatSupplierRate, averagePaymentTime, businessGrowth, riskLevel.\n    Usage Notes: Read-only. Data is generated entirely server-side; this\n    component never accepts manual input for these fields.\n\n================================================================================\n4. SUPPLIER COMPONENTS\n================================================================================\n\n4.1 SupplierSummaryCard\n    Purpose: Dashboard summary of the supplier\'s account.\n    Props: supplierName, category, verificationStatus.\n\n4.2 CustomerCard\n    Purpose: Represent a business customer in enquiry or order contexts,\n    respecting Business Privacy rules (Document 09).\n    Props: displayName ("Verified Business" or "ABC Store (Verified)"),\n    verificationStatus, lastInteractionDate, onPress.\n    Usage Notes: Must never render full, unmasked business identity details\n    beyond what the platform\'s privacy rules permit.\n\n4.3 ProductManagementCard\n    Purpose: Represent a product in the supplier\'s own catalogue management\n    view, with edit/status controls.\n    Props: productName, price, stockStatus, isPublished, onEdit, onToggle\n    Availability.\n\n4.4 OrderCard (Supplier view)\n    Purpose: Represent a single incoming or historical order in the\n    supplier\'s order list.\n    Props: orderId, customerDisplayName, status, totalAmount, orderDate,\n    onAccept, onReject, onPress.\n    States: new/incoming, accepted, in-fulfilment, completed, cancelled.\n\n4.5 BusinessPerformanceCard\n    Purpose: Present supplier-facing performance statistics (see Document\n    07 for underlying metrics).\n    Props: activeSince, businessesServed, ordersCompleted, repeatCustomer\n    Rate, averageResponseTime, responseRate, verificationStatus.\n\n4.6 BusinessUpdateComposer\n    Purpose: Allow a supplier to publish a Business Update.\n    Props: updateType (new product / promotion / price update / hours /\n    location / announcement), content, onPublish.\n\n================================================================================\n5. SHARED COMPONENTS\n================================================================================\n\n5.1 AppHeader\n    Purpose: Persistent header used across top-level tab screens.\n    Props: title, showNotificationIcon, showProfileIcon, onNotificationPress,\n    onProfilePress.\n\n5.2 SearchBar\n    Purpose: Text-based search entry point for suppliers, products, or\n    orders depending on context.\n    Props: placeholder, value, onChangeText, onSubmit, onFilterPress.\n\n5.3 BottomNavigation\n    Purpose: Primary tab navigation, rendered conditionally based on\n    authenticated role.\n    Props: activeTab, role (business | supplier), onTabPress.\n\n5.4 StatisticsCard\n    Purpose: Generic single-metric display card used by both\n    DigitalBusinessProfileCard and BusinessPerformanceCard.\n    Props: label, value, trendDirection (optional), trendValue (optional).\n\n5.5 NotificationCard\n    Purpose: Represent a single notification in the notification list.\n    Props: notificationType, message, timestamp, isRead, onPress.\n    States: unread, read.\n\n5.6 VerificationBadge\n    Purpose: Consistent visual indicator of verified status, used across\n    Business Cards, Supplier Cards, and profile headers.\n    Props: isVerified.\n    Usage Notes: Always paired with icon + text label, never colour alone\n    (accessibility requirement, Document 02 Section 13).\n\n5.7 CategoryChips\n    Purpose: Horizontally scrollable filter/browse control.\n    Props: categories (list), selectedCategory(ies), onSelect,\n    multiSelect (boolean).\n\n5.8 ActionButton\n    Purpose: Generic button component supporting Primary, Secondary,\n    Tertiary, and Destructive visual variants (Document 02, Section 8).\n    Props: label, variant, onPress, isLoading, isDisabled.\n\n5.9 EmptyState\n    Purpose: Consistent placeholder for any list-based screen with no\n    content.\n    Props: icon, message, actionLabel (optional), onActionPress (optional).\n\n5.10 LoadingState\n    Purpose: Consistent skeleton-loading placeholder matching the shape of\n    pending content (card skeleton, list skeleton, profile skeleton).\n    Props: variant (card | list | profile), count.\n\n5.11 Modal\n    Purpose: Generic overlay container for short-lived focused tasks (e.g.\n    filter selection, image preview).\n    Props: isVisible, onClose, children.\n\n5.12 Dialog\n    Purpose: Confirmation prompt for destructive or high-consequence\n    actions (Document 02, Section 2.4).\n    Props: title, message, confirmLabel, cancelLabel, onConfirm, onCancel.\n\n================================================================================\n6. COMPONENT REUSE RULES\n================================================================================\n\n    1. No screen may implement its own one-off version of a component\n       listed above; all variations must be expressed through props.\n    2. Role-specific components (Business vs Supplier) must share the same\n       underlying visual shell (card structure, spacing, typography) as\n       defined in Document 02, differing only in content and available\n       actions.\n    3. Any new component required during development must be proposed as\n       an addition to this document before implementation, to preserve a\n       single, consistent component library as the codebase scales.\n',
    '04_DATABASE_DESIGN.txt': '================================================================================\n                            TRU CONNECT\n                        DATABASE DESIGN\n                          Document 04\n================================================================================\n\nDatabase Engine: PostgreSQL\nVersion: 2.0 (Domain Architecture Revision)\nRelated Documents: 05_BACKEND_API_SPECIFICATION.txt,\n                    07_DATA_AND_TRUST_ENGINE.txt\n\nNote: This document describes entities, attributes, and relationships in\nplain language for architectural planning. It intentionally contains no SQL\nDDL, per project instructions. Primary keys are assumed to be UUIDs unless\notherwise noted; all entities include created_at and updated_at timestamps\nunless otherwise noted.\n\n================================================================================\n1. OVERVIEW\n================================================================================\n\nTRU Connect\'s data model is organised into seven logical domains, each\nowning a specific business capability. This replaces the flat entity list\nused in earlier drafts of this document with a structure that maps\ndirectly onto the platform\'s functional areas (authentication, business,\nsupplier, marketplace, trust, verification, platform).\n\nAll domains currently share a single PostgreSQL "public" schema and a\nsingle database instance. The domain boundaries are logical, not physical,\nbut are deliberately drawn so that each domain could later be extracted\ninto its own schema, or even its own service/database, with minimal\nredesign — consistent with the Scalable Architecture principle (Document\n01, Section 10).\n\n================================================================================\n2. DOMAIN INDEX\n================================================================================\n\n    4.1  Authentication Domain\n    4.2  Business Domain\n    4.3  Supplier Domain\n    4.4  Marketplace Domain\n    4.5  Trust Domain\n    4.6  Verification Domain\n    4.7  Platform Domain\n\nSection numbers below intentionally mirror the domain numbering (4.1–4.7)\nused across this document and Document 05, so the two documents can be\ncross-referenced directly by domain.\n\n================================================================================\n4. DATABASE DOMAIN ARCHITECTURE\n================================================================================\n\nThe TRU Connect database is organised into logical business domains rather\nthan physical PostgreSQL schemas.\n\nEach domain owns a specific business capability and groups related tables\ntogether to improve maintainability, readability, and future scalability.\n\nAlthough all tables currently reside within the PostgreSQL public schema,\nthis logical organisation allows the platform to evolve into separate\ndatabase schemas or services in the future without requiring significant\nredesign.\n\n--------------------------------------------------------------------------------\n4.1 Authentication Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nManages user identity, authentication, authorisation, and account security.\n\nTables\n------\n    - users\n    - roles\n    - permissions\n    - role_permissions\n    - user_roles\n    - refresh_tokens\n    - login_history\n    - password_reset_tokens\n\nTable Definitions\n------------------\n\nusers\n    - id\n    - email\n    - phone_number (nullable; reserved for future phone login)\n    - password_hash (nullable when authenticated via Google only)\n    - google_id (nullable)\n    - is_active\n    - last_login_at\n    - created_at / updated_at\n    Notes: role assignment is no longer a fixed enum column on users; it is\n    modelled through user_roles/roles below, allowing a single account to\n    hold multiple roles in future (e.g. a Platform Administrator role,\n    Document 01 Section 9.3) without a schema change.\n\nroles\n    - id\n    - name (e.g. business, supplier, admin, financial_partner)\n    - description\n\npermissions\n    - id\n    - name (e.g. manage_own_products, review_verification, view_audit_logs)\n    - description\n\nrole_permissions\n    - role_id (FK -> roles)\n    - permission_id (FK -> permissions)\n    Join table; composite primary key (role_id, permission_id).\n\nuser_roles\n    - user_id (FK -> users)\n    - role_id (FK -> roles)\n    Join table; composite primary key (user_id, role_id). In Phase 1, a\n    user is expected to hold exactly one of the "business" or "supplier"\n    roles, enforced at the application layer; the schema itself does not\n    prevent multi-role accounts, anticipating future admin/partner roles.\n\nrefresh_tokens\n    - id\n    - user_id (FK -> users)\n    - token_hash\n    - expires_at\n    - revoked_at (nullable)\n    - created_at\n\nlogin_history\n    - id\n    - user_id (FK -> users)\n    - ip_address\n    - user_agent\n    - login_at\n    - success (boolean)\n    Usage Notes: supports security auditing and can additionally feed\n    anomaly-detection signals for the Trust Domain in later phases (e.g.\n    unusual login patterns as a risk signal).\n\npassword_reset_tokens\n    - id\n    - user_id (FK -> users)\n    - token_hash\n    - expires_at\n    - used_at (nullable)\n\n--------------------------------------------------------------------------------\n4.2 Business Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nStores all information related to businesses using TRU Connect.\n\nTables\n------\n    - businesses\n    - business_profiles\n    - business_addresses\n    - business_categories\n    - business_documents\n    - business_settings\n    - business_bookmarks\n\nTable Definitions\n------------------\n\nbusinesses\n    - id\n    - user_id (FK -> users)\n    - business_name\n    - registered_since (used for "Business Since" display)\n    - is_verified (denormalised flag; source of truth is\n      verification_requests in the Verification Domain)\n    - created_at / updated_at\n\nbusiness_profiles\n    - id\n    - business_id (FK -> businesses, 1:1)\n    - orders_count\n    - suppliers_count\n    - average_order_value\n    - largest_order_value\n    - repeat_supplier_rate\n    - average_payment_time_days\n    - business_growth_percentage\n    - risk_level (enum: low, medium, high)\n    - last_calculated_at\n    Notes: this is the Digital Business Profile described in Document 07.\n    It stores current, display-ready derived values; historical trend data\n    lives in trust_score_history (Trust Domain, 4.5). Populated and updated\n    exclusively by background recalculation jobs (Document 06, Section\n    15) — never edited directly by the business user.\n\nbusiness_addresses\n    - id\n    - business_id (FK -> businesses)\n    - address_line\n    - city_id (FK -> cities, Platform Domain)\n    - province_id (FK -> provinces, Platform Domain)\n    - latitude\n    - longitude\n    - is_primary (boolean)\n    Notes: a business may hold multiple addresses (e.g. multiple outlets);\n    orders reference a specific business_address as the delivery address.\n\nbusiness_categories\n    - id\n    - business_id (FK -> businesses)\n    - category_id (FK -> lookup_categories, Platform Domain)\n    Join table; supports a business belonging to more than one category if\n    needed, while defaulting to a single primary category at registration.\n\nbusiness_documents\n    - id\n    - business_id (FK -> businesses)\n    - document_type (e.g. business_registration, tax_certificate, id_copy)\n    - file_url\n    - uploaded_at\n    Notes: distinct from verification_documents (Verification Domain);\n    business_documents supports the general "Business Documents" screen\n    (Document 01, Section 8.2), while verification_documents specifically\n    supports an active verification review workflow. A document may be\n    referenced by both in practice.\n\nbusiness_settings\n    - id\n    - business_id (FK -> businesses, 1:1)\n    - preferred_language\n    - preferred_currency\n    - default_delivery_address_id (FK -> business_addresses, nullable)\n    - other app-level preferences as required\n\nbusiness_bookmarks\n    - id\n    - business_id (FK -> businesses)\n    - supplier_id (FK -> suppliers)\n    - created_at\n    Notes: represents a business saving/following a supplier. See Section\n    4.4 (saved_suppliers) for an important clarification on how this table\n    relates to the Marketplace Domain\'s saved-item tables.\n    Constraint: unique on (business_id, supplier_id).\n\n--------------------------------------------------------------------------------\n4.3 Supplier Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nStores supplier information, catalogues, products, and supplier\noperations.\n\nTables\n------\n    - suppliers\n    - supplier_profiles\n    - supplier_categories\n    - supplier_products\n    - supplier_product_images\n    - supplier_delivery_regions\n    - supplier_business_hours\n    - supplier_updates\n\nTable Definitions\n------------------\n\nsuppliers\n    - id\n    - user_id (FK -> users)\n    - supplier_name\n    - active_since (used for "Active Since" display)\n    - is_verified (denormalised flag; source of truth is\n      verification_requests in the Verification Domain)\n    - created_at / updated_at\n\nsupplier_profiles\n    - id\n    - supplier_id (FK -> suppliers, 1:1)\n    - businesses_served_count\n    - orders_completed_count\n    - repeat_customer_rate\n    - average_response_time_minutes\n    - response_rate_percentage\n    - last_calculated_at\n    Notes: current, display-ready supplier performance statistics\n    (Document 07); historical trend data lives in trust_score_history\n    (Trust Domain, 4.5).\n\nsupplier_categories\n    - id\n    - supplier_id (FK -> suppliers)\n    - category_id (FK -> lookup_categories, Platform Domain)\n    Join table; supports a supplier belonging to more than one category.\n\nsupplier_products\n    - id\n    - supplier_id (FK -> suppliers)\n    - category_id (FK -> lookup_categories, Platform Domain)\n    - name\n    - description\n    - price\n    - unit (e.g. each, case, kg)\n    - bulk_pricing_rules (structured; may be normalised into a separate\n      table if multiple price tiers are required)\n    - minimum_order_quantity\n    - stock_status (enum: in_stock, low_stock, out_of_stock)\n    - is_published\n    - created_at / updated_at\n    Notes: previously referred to simply as "Products" in earlier drafts;\n    renamed to supplier_products to make domain ownership explicit.\n\nsupplier_product_images\n    - id\n    - product_id (FK -> supplier_products)\n    - image_url\n    - sort_order\n    Notes: normalises product imagery out of supplier_products to support\n    multiple images per product without repeating columns.\n\nsupplier_delivery_regions\n    - id\n    - supplier_id (FK -> suppliers)\n    - province_id (FK -> provinces, Platform Domain, nullable)\n    - city_id (FK -> cities, Platform Domain, nullable)\n    - region_description (free-text fallback for areas not covered by the\n      provinces/cities lookup)\n    Notes: supports the "regions served" concept referenced in Document 06,\n    Section 2, as a structured, queryable set rather than a single field.\n\nsupplier_business_hours\n    - id\n    - supplier_id (FK -> suppliers)\n    - day_of_week (enum: monday–sunday)\n    - open_time\n    - close_time\n    - is_closed (boolean, for days with no trading hours)\n\nsupplier_updates\n    - id\n    - supplier_id (FK -> suppliers)\n    - update_type (enum: new_product, promotion, price_update, hours,\n      new_location, announcement)\n    - content\n    - published_at\n    - expires_at (nullable, e.g. for time-bound promotions)\n    Notes: previously referred to as "Business Updates" in earlier drafts;\n    renamed to supplier_updates to make domain ownership explicit and to\n    avoid naming collision with businesses.\n\n--------------------------------------------------------------------------------\n4.4 Marketplace Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nContains all marketplace interactions between businesses and suppliers.\n\nTables\n------\n    - orders\n    - order_items\n    - business_questions\n    - supplier_responses\n    - product_views\n    - saved_products\n    - saved_suppliers\n\nTable Definitions\n------------------\n\norders\n    - id\n    - business_id (FK -> businesses)\n    - supplier_id (FK -> suppliers)\n    - status (enum: pending, accepted, rejected, in_fulfilment, completed,\n      cancelled)\n    - total_amount\n    - placed_at\n    - accepted_at (nullable)\n    - completed_at (nullable)\n    - cancelled_at (nullable)\n    - delivery_address_id (FK -> business_addresses, Business Domain)\n    - delivery_tracking_reference (nullable)\n\norder_items\n    - id\n    - order_id (FK -> orders)\n    - product_id (FK -> supplier_products, Supplier Domain)\n    - quantity\n    - unit_price_at_order_time (captured at time of order to preserve\n      historical accuracy independent of later price changes)\n    - line_total\n\nbusiness_questions\n    - id\n    - product_id (FK -> supplier_products, Supplier Domain)\n    - business_id (FK -> businesses)\n    - question_text\n    - question_category (enum: availability, delivery, pricing, bulk_order,\n      packaging, specifications, general)\n    - created_at\n    Notes: central to the "Business Conversations" model (Document 09).\n    Has zero or one supplier_response.\n\nsupplier_responses\n    - id\n    - business_question_id (FK -> business_questions, 1:1)\n    - supplier_id (FK -> suppliers)\n    - response_text\n    - responded_at\n\nproduct_views\n    - id\n    - business_id (FK -> businesses)\n    - product_id (FK -> supplier_products, Supplier Domain)\n    - viewed_at\n    Notes: explicit event log backing the "Recently Viewed" feature\n    (Document 01, Section 7.4) and product/supplier popularity ranking. Feeds\n    the Trust Domain as a discovery/interest signal (Document 07, Section\n    5) without directly affecting business risk/trust scoring.\n\nsaved_products\n    - id\n    - business_id (FK -> businesses)\n    - product_id (FK -> supplier_products, Supplier Domain)\n    - created_at\n    Notes: allows a business to save individual products, independent of\n    saving the supplier as a whole. Constraint: unique on (business_id,\n    product_id).\n\nsaved_suppliers\n    - id\n    - business_id (FK -> businesses)\n    - supplier_id (FK -> suppliers)\n    - created_at\n    Notes: this is the operational "save/follow a supplier" relationship\n    consumed by the Suppliers tab, the notification-of-Business-Updates\n    workflow (Document 06, Section 9), and the Digital Business Profile\'s\n    "Saved Suppliers" list. Constraint: unique on (business_id,\n    supplier_id).\n\n    Relationship to business_bookmarks (Business Domain, 4.2): to avoid\n    ambiguity between these two similarly-purposed tables, the following\n    division of responsibility applies —\n        - business_bookmarks is the general-purpose bookmarking table\n          owned by the Business Domain, intended to support bookmarking of\n          multiple entity types over time (suppliers today; potentially\n          products, categories, or Business Updates in future releases)\n          via a polymorphic or typed reference.\n        - saved_suppliers is the specific, high-frequency, marketplace-\n          facing join table optimised for the one well-defined "follow a\n          supplier" interaction and its downstream effects (notifications,\n          discovery ranking).\n    Phase 1 implementation should treat saved_suppliers as the single\n    source of truth actually driving product behaviour; business_bookmarks\n    may be introduced alongside it or deferred until a second bookmarkable\n    entity type is required, to avoid maintaining two systems for an\n    identical Phase 1 use case.\n\n--------------------------------------------------------------------------------\n4.5 Trust Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nStores relationship intelligence and behavioural trust data generated from\nbusiness activity across the platform.\n\nTables\n------\n    - business_supplier_relationships\n    - relationship_events\n    - trust_signals\n    - business_health_scores\n    - supplier_reputation_scores\n    - trust_score_history\n\nTable Definitions\n------------------\n\nbusiness_supplier_relationships\n    - id\n    - business_id (FK -> businesses, Business Domain)\n    - supplier_id (FK -> suppliers, Supplier Domain)\n    - first_interaction_at\n    - last_interaction_at\n    - total_orders\n    - total_order_value\n    - relationship_health_score\n    Notes: previously referred to simply as "Relationships"; renamed to\n    business_supplier_relationships for domain clarity. Constraint: unique\n    on (business_id, supplier_id). This is the fundamental unit of trust\n    described in Document 07, Section 3.\n\nrelationship_events\n    - id\n    - relationship_id (FK -> business_supplier_relationships)\n    - event_type (enum: order_placed, order_accepted, order_completed,\n      order_cancelled, order_rejected, question_asked, response_received)\n    - event_value (nullable numeric payload, e.g. order value)\n    - occurred_at\n    Notes: a granular, append-only event log per relationship, providing\n    the raw input for relationship_health_score recalculation and for any\n    future audit or model-training needs, without requiring\n    business_supplier_relationships itself to store full history.\n\ntrust_signals\n    - id\n    - owner_type (enum: business, supplier)\n    - owner_id (polymorphic reference to businesses or suppliers)\n    - signal_type (e.g. repeat_order_rate, verification_status,\n      response_rate, cancellation_rate, payment_consistency)\n    - signal_value\n    - calculated_at\n    Notes: the normalised, queryable store of the individual Trust Signals\n    and Risk Signals described in Document 07, Sections 6–8, decoupled\n    from the specific display-ready fields in business_profiles /\n    supplier_profiles so that new signal types can be added without\n    schema migrations to those tables.\n\nbusiness_health_scores\n    - id\n    - business_id (FK -> businesses, Business Domain)\n    - score\n    - calculated_at\n    - methodology_version\n    Notes: stores the current, versioned Business Health Score described\n    in Document 07, Section 10. Kept separate from business_profiles so\n    that the scoring methodology can evolve (methodology_version) without\n    disrupting the simpler display fields businesses see day-to-day.\n\nsupplier_reputation_scores\n    - id\n    - supplier_id (FK -> suppliers, Supplier Domain)\n    - score\n    - calculated_at\n    - methodology_version\n    Notes: mirrors business_health_scores for suppliers, backing the\n    Supplier Reputation concept in Document 07, Section 11.\n\ntrust_score_history\n    - id\n    - owner_type (enum: business, supplier)\n    - owner_id (polymorphic reference to businesses or suppliers)\n    - score_type (enum: business_health, supplier_reputation)\n    - score_value\n    - recorded_at\n    Notes: append-only time series enabling trend displays (e.g. "Business\n    Growth +37%") and future model back-testing, distinct from the\n    single-current-value fields in business_health_scores /\n    supplier_reputation_scores.\n\n--------------------------------------------------------------------------------\n4.6 Verification Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nManages verification of businesses, suppliers, and supporting documents.\n\nTables\n------\n    - verification_requests\n    - verification_documents\n    - verification_history\n\nTable Definitions\n------------------\n\nverification_requests\n    - id\n    - owner_type (enum: business, supplier)\n    - owner_id (polymorphic reference to businesses or suppliers)\n    - verification_type (e.g. identity, business_registration, address)\n    - status (enum: pending, approved, rejected)\n    - submitted_at\n    - reviewed_at (nullable)\n    - reviewer_notes (internal only, never exposed to end users)\n    Notes: previously referred to as "Verification Records"; renamed to\n    verification_requests to better reflect the request/review lifecycle\n    described in Document 06, Section 3.\n\nverification_documents\n    - id\n    - verification_request_id (FK -> verification_requests)\n    - document_type\n    - file_url\n    - uploaded_at\n    Notes: distinct from business_documents (Business Domain); this table\n    is scoped specifically to documents submitted in support of an active\n    verification_request.\n\nverification_history\n    - id\n    - verification_request_id (FK -> verification_requests)\n    - previous_status\n    - new_status\n    - changed_at\n    - changed_by (nullable reference to an internal reviewing user/admin)\n    Notes: append-only audit trail of status transitions on a verification\n    request, supporting compliance and dispute resolution.\n\n--------------------------------------------------------------------------------\n4.7 Platform Domain\n--------------------------------------------------------------------------------\n\nPurpose\n-------\nSupports platform-wide services and administration.\n\nTables\n------\n    - notifications\n    - notification_preferences\n    - audit_logs\n    - system_settings\n    - lookup_categories\n    - provinces\n    - cities\n\nTable Definitions\n------------------\n\nnotifications\n    - id\n    - user_id (FK -> users, Authentication Domain)\n    - notification_type (enum: order_update, question_response,\n      supplier_update, system, verification_update)\n    - title\n    - body\n    - related_entity_type (nullable; e.g. order, product, business_question)\n    - related_entity_id (nullable)\n    - is_read\n    - created_at\n\nnotification_preferences\n    - id\n    - user_id (FK -> users, Authentication Domain)\n    - notification_type (enum: matches notifications.notification_type)\n    - is_enabled (boolean)\n    - channel (enum: push, email, sms)\n    Notes: allows a user to opt out of specific notification types per\n    channel, rather than an all-or-nothing setting.\n\naudit_logs\n    - id\n    - user_id (FK -> users, nullable for system-initiated actions)\n    - action (e.g. product_updated, order_cancelled, verification_reviewed)\n    - entity_type\n    - entity_id\n    - metadata (structured, e.g. before/after values where relevant)\n    - created_at\n    Notes: platform-wide administrative audit trail, distinct from the\n    domain-specific relationship_events (Trust Domain) and\n    verification_history (Verification Domain), which serve business-\n    logic purposes rather than general administrative auditing.\n\nsystem_settings\n    - id\n    - key\n    - value\n    - description\n    - updated_at\n    Notes: generic key-value store for platform configuration (e.g.\n    feature flags, minimum app version, scoring methodology toggles)\n    that should not require a code deployment to change.\n\nlookup_categories\n    - id\n    - name\n    - parent_category_id (nullable, self-referencing FK, supports category\n      hierarchies)\n    - applies_to (enum: business, supplier, product)\n    Notes: previously referred to simply as "Categories"; renamed to\n    lookup_categories to reflect its role as a shared platform lookup\n    table, referenced by business_categories, supplier_categories, and\n    supplier_products.\n\nprovinces\n    - id\n    - name\n\ncities\n    - id\n    - name\n    - province_id (FK -> provinces)\n    Notes: provinces and cities together back business_addresses and\n    supplier_delivery_regions, supporting structured location filtering\n    for supplier discovery (Document 06, Section 5).\n\n================================================================================\n5. CROSS-DOMAIN RELATIONSHIP SUMMARY\n================================================================================\n\n    - Authentication Domain -> Business/Supplier Domains: users.id is\n      referenced by exactly one of businesses.user_id or suppliers.user_id\n      per account in Phase 1.\n    - Business Domain -> Marketplace Domain: businesses.id is referenced by\n      orders, business_questions, saved_products, saved_suppliers, and\n      product_views.\n    - Supplier Domain -> Marketplace Domain: suppliers.id is referenced by\n      orders and supplier_responses; supplier_products.id is referenced by\n      order_items, business_questions, product_views, and saved_products.\n    - Business Domain + Supplier Domain -> Trust Domain:\n      business_supplier_relationships is the join entity connecting a\n      specific business and supplier, with relationship_events,\n      trust_signals, business_health_scores, and supplier_reputation_scores\n      all deriving from activity recorded in the Marketplace Domain.\n    - Business/Supplier Domains -> Verification Domain:\n      verification_requests uses a polymorphic owner_type/owner_id\n      reference back to either businesses or suppliers.\n    - All Domains -> Platform Domain: notifications reference users\n      directly; lookup_categories, provinces, and cities are shared\n      reference data consumed by the Business and Supplier Domains.\n\n================================================================================\n6. FUTURE-SCOPED ENTITIES (PLACEHOLDERS)\n================================================================================\n\nThese are documented now, per the roadmap in Document 08, so that current\ndomain and schema design does not preclude their addition later. They are\nexpected to form a new Financial Domain alongside the seven domains above\nonce Phase 2/3 begins.\n\n6.1 Wallets (Phase 2) — Financial Domain (future)\n    - id, owner_type, owner_id, balance, currency, status\n\n6.2 Wallet Transactions (Phase 2) — Financial Domain (future)\n    - id, wallet_id, type (credit/debit), amount, related_order_id,\n      created_at\n\n6.3 Credit Applications / Trade Finance (Phase 3) — Financial Domain (future)\n    - id, business_id or supplier_id, requested_amount, status,\n      risk_assessment_reference, decision_at\n\nThe Financial Domain will consume trust_signals, business_health_scores,\nand supplier_reputation_scores from the Trust Domain as its primary risk-\nassessment inputs, avoiding duplication of trust logic within the new\ndomain.\n\n================================================================================\n7. RELATIONAL DESIGN NOTES\n================================================================================\n\n    1. Businesses and Suppliers are deliberately modelled as separate\n       domains and separate core tables, rather than a single polymorphic\n       "accounts" table with a type flag, because their attributes and\n       downstream domain relationships (e.g. supplier_delivery_regions,\n       business_addresses) diverge significantly and are expected to\n       diverge further as the roadmap progresses.\n    2. business_profiles/supplier_profiles are kept separate from\n       business_health_scores/supplier_reputation_scores: the former hold\n       simple, current, display-ready statistics consumed directly by the\n       mobile UI (Document 03); the latter hold versioned, methodology-\n       aware scores intended for risk assessment and future underwriting,\n       allowing the scoring methodology to evolve independently of the\n       UI-facing profile fields.\n    3. All monetary values should be stored using a fixed-point/decimal\n       type, never floating point, to avoid rounding errors in financial\n       reporting.\n    4. All foreign keys should enforce referential integrity at the\n       database level; soft-deletes (an is_deleted / deleted_at column)\n       should be used in place of hard deletes for businesses, suppliers,\n       orders, and verification_requests, to preserve the historical\n       integrity of the Trust Domain\'s data.\n    5. Authorisation logic should prefer the roles/permissions/\n       role_permissions/user_roles structure (Authentication Domain) over\n       hard-coded role checks in application code, so that future roles\n       (e.g. Platform Administrator, Financial Partner — Document 01,\n       Section 9.3) can be introduced by inserting data rather than\n       shipping new code paths.\n    6. Where two tables appear to serve a similar purpose across domains\n       (e.g. business_bookmarks vs. saved_suppliers, Section 4.4), the\n       documented division of responsibility should be followed rather\n       than treating the tables as interchangeable, to avoid divergent or\n       duplicated state.\n',
    '05_BACKEND_API_SPECIFICATION.txt': '================================================================================\n                            TRU CONNECT\n                  BACKEND API SPECIFICATION\n                          Document 05\n================================================================================\n\nBackend Framework: Python Flask\nArchitecture: REST API\nAuthentication: JWT + Google Authentication\nVersion: 2.0 (Domain Architecture Revision)\nRelated Documents: 04_DATABASE_DESIGN.txt, 06_BUSINESS_RULES_AND_WORKFLOWS.txt\n\nNote: Endpoints are described conceptually (resource, method, purpose,\nrequired role) rather than in code. Standard REST conventions apply\nthroughout: collection endpoints for lists, resource endpoints for single\nitems, standard HTTP status codes, and pagination on all list responses.\n\nThis revision reorganises the API surface to mirror the seven database\ndomains defined in Document 04 (Sections 4.1–4.7), so that each domain\'s\nendpoints, tables, and ownership boundaries stay aligned as the platform\ngrows.\n\n================================================================================\n1. GENERAL API CONVENTIONS\n================================================================================\n\n    - All endpoints are prefixed under a versioned base path (e.g. /api/v1).\n    - All authenticated endpoints require a valid JWT bearer token.\n    - Role-restricted endpoints validate the authenticated user\'s role(s)\n      via the roles/user_roles/permissions structure (Document 04, Section\n      4.1) before processing, rather than a hard-coded role check.\n    - All list endpoints support pagination (page, page_size) and return\n      total count metadata.\n    - All timestamps are returned in ISO 8601 / UTC.\n    - Errors follow a consistent structure: error code, human-readable\n      message, and optional field-level validation details.\n    - Endpoint groupings below are numbered 5.1–5.7 to align directly with\n      the domain numbering in Document 04 (4.1–4.7).\n\n================================================================================\n5.1 AUTHENTICATION DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: users, roles, permissions, role_permissions, user_roles,\nrefresh_tokens, login_history, password_reset_tokens.\n\n    POST   /auth/register              Create a new account (business or\n                                        supplier role assigned via\n                                        user_roles at registration).\n    POST   /auth/login                 Authenticate with email/password;\n                                        records a login_history entry;\n                                        returns JWT + refresh token.\n    POST   /auth/google                Authenticate/register via Google\n                                        OAuth token; returns JWT + refresh\n                                        token.\n    POST   /auth/refresh                Exchange a valid refresh_token for\n                                        a new JWT.\n    POST   /auth/logout                 Revoke the current refresh_token.\n    POST   /auth/forgot-password        Initiate password reset flow;\n                                        creates a password_reset_tokens\n                                        entry.\n    POST   /auth/reset-password         Complete password reset flow using\n                                        a valid reset token.\n    GET    /auth/me/roles               List roles assigned to the\n                                        authenticated user (supports future\n                                        multi-role accounts, e.g. admin).\n    GET    /auth/me/login-history       List recent login_history entries\n                                        for the authenticated user (self-\n                                        service security review).\n\n    Future: /auth/phone/request-otp, /auth/phone/verify-otp,\n    /auth/biometric/register, /auth/biometric/verify, /auth/passkey/*.\n\n    Admin-only (future role, Document 01 Section 9.3):\n    GET    /admin/roles                 List roles and permissions.\n    PUT    /admin/users/{id}/roles       Assign/revoke a role for a user.\n\n================================================================================\n5.2 BUSINESS DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: businesses, business_profiles, business_addresses,\nbusiness_categories, business_documents, business_settings,\nbusiness_bookmarks.\n\n    GET    /businesses/me                 Get authenticated business\'s own\n                                          profile (businesses +\n                                          business_settings).\n    PUT    /businesses/me                 Update own business profile.\n    GET    /businesses/me/dashboard       Aggregated dashboard payload:\n                                          today\'s orders, pending orders,\n                                          nearby suppliers, recommended\n                                          products, recent activity\n                                          (composed from Marketplace and\n                                          Trust Domain data).\n    GET    /businesses/me/profile         Get own Digital Business Profile\n                                          (business_profiles — read-only,\n                                          system-generated).\n    GET    /businesses/{id}                Get public-safe view of a\n                                          business (supplier-facing,\n                                          respecting Business Privacy\n                                          rules — Document 09).\n\n    GET    /businesses/me/addresses        List own business_addresses.\n    POST   /businesses/me/addresses        Add a new business address.\n    PUT    /businesses/me/addresses/{id}   Update a business address.\n    DELETE /businesses/me/addresses/{id}   Remove a business address.\n    PUT    /businesses/me/addresses/{id}/primary\n                                          Set an address as primary/\n                                          default.\n\n    GET    /businesses/me/categories       List own business_categories.\n    PUT    /businesses/me/categories       Update own business category\n                                          assignment(s).\n\n    GET    /businesses/me/documents        List own business_documents.\n    POST   /businesses/me/documents        Upload a new business document.\n    DELETE /businesses/me/documents/{id}   Remove a business document.\n\n    GET    /businesses/me/settings         Get own business_settings.\n    PUT    /businesses/me/settings         Update own business_settings.\n\n    POST   /businesses/me/bookmarks        Create a business_bookmarks\n                                          entry (general-purpose\n                                          bookmarking; see Document 04,\n                                          Section 4.4 for its relationship\n                                          to saved_suppliers).\n    DELETE /businesses/me/bookmarks/{id}   Remove a bookmark.\n    GET    /businesses/me/bookmarks        List own bookmarks.\n\n================================================================================\n5.3 SUPPLIER DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: suppliers, supplier_profiles, supplier_categories,\nsupplier_products, supplier_product_images, supplier_delivery_regions,\nsupplier_business_hours, supplier_updates.\n\n    GET    /suppliers/me                  Get authenticated supplier\'s own\n                                          profile.\n    PUT    /suppliers/me                  Update own supplier profile.\n    GET    /suppliers/me/dashboard        Aggregated dashboard payload:\n                                          today\'s orders, customer\n                                          enquiries, recent orders, top\n                                          products, business performance\n                                          (composed from Marketplace and\n                                          Trust Domain data).\n    GET    /suppliers/me/performance      Get own supplier_profiles\n                                          performance statistics.\n    GET    /suppliers                     List/search suppliers (business-\n                                          facing discovery), supports\n                                          filters: category, province,\n                                          city, verified_only, keyword.\n    GET    /suppliers/{id}                Get public supplier profile\n                                          (business-facing view: profile,\n                                          verification, products, business\n                                          questions, updates, statistics).\n    GET    /suppliers/featured             Featured suppliers list.\n    GET    /suppliers/nearby               Nearby suppliers based on\n                                          business location\n                                          (business_addresses ->\n                                          supplier_delivery_regions match).\n\n    GET    /suppliers/me/categories        List own supplier_categories.\n    PUT    /suppliers/me/categories        Update own supplier category\n                                          assignment(s).\n\n    GET    /suppliers/me/delivery-regions  List own\n                                          supplier_delivery_regions.\n    POST   /suppliers/me/delivery-regions  Add a delivery region.\n    DELETE /suppliers/me/delivery-regions/{id}\n                                          Remove a delivery region.\n\n    GET    /suppliers/me/business-hours    List own\n                                          supplier_business_hours.\n    PUT    /suppliers/me/business-hours    Update business hours (full\n                                          week payload).\n\n    GET    /products                      Search/list supplier_products,\n                                          supports filters: category,\n                                          supplier_id, keyword, price\n                                          range.\n    GET    /products/popular              Popular products listing.\n    GET    /products/recommended          Recommended products for the\n                                          authenticated business.\n    GET    /products/{id}                 Get product detail, including\n                                          attached business_questions\n                                          thread and supplier_product_\n                                          images.\n    POST   /products                      Create a supplier_products entry\n                                          (supplier only).\n    PUT    /products/{id}                 Update a product (supplier only,\n                                          own product).\n    DELETE /products/{id}                 Soft-delete/unpublish a product\n                                          (supplier only, own product).\n    PUT    /products/{id}/availability    Toggle stock_status (supplier\n                                          only).\n    POST   /products/{id}/images           Add a supplier_product_images\n                                          entry.\n    DELETE /products/{id}/images/{image_id}\n                                          Remove a product image.\n\n    POST   /supplier-updates               Publish a new supplier_updates\n                                          entry (supplier only).\n    GET    /supplier-updates/mine           List own published updates\n                                          (supplier only).\n    GET    /suppliers/{id}/updates          List a supplier\'s published\n                                          updates (business-facing, public\n                                          view).\n\n================================================================================\n5.4 MARKETPLACE DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: orders, order_items, business_questions,\nsupplier_responses, product_views, saved_products, saved_suppliers.\n\n    POST   /orders                        Place a new order (business\n                                          only). Payload includes supplier\n                                          id, order items (product id +\n                                          quantity), delivery_address_id.\n    GET    /orders                        List orders for the authenticated\n                                          user (business: own placed\n                                          orders; supplier: own received\n                                          orders), filterable by status.\n    GET    /orders/{id}                   Get order detail, including\n                                          order_items and delivery tracking\n                                          status.\n    PUT    /orders/{id}/accept             Accept an order (supplier only).\n    PUT    /orders/{id}/reject             Reject an order (supplier only,\n                                          requires reason).\n    PUT    /orders/{id}/cancel             Cancel an order (business only,\n                                          subject to workflow rules —\n                                          Document 06).\n    PUT    /orders/{id}/complete           Mark an order as completed\n                                          (supplier only, or system-\n                                          triggered on delivery\n                                          confirmation).\n    GET    /orders/{id}/invoice            Retrieve invoice for a completed\n                                          order.\n    GET    /orders/{id}/tracking           Retrieve delivery tracking\n                                          status.\n\n    POST   /products/{id}/questions        Submit a business_questions\n                                          entry on a product (business\n                                          only).\n    GET    /products/{id}/questions        List business_questions and\n                                          their supplier_responses for a\n                                          product (public — supports\n                                          supplier discovery use case in\n                                          Document 09).\n    POST   /questions/{id}/responses       Submit a supplier_responses\n                                          entry (supplier only, must own\n                                          the related product).\n    GET    /businesses/me/questions        List questions asked by the\n                                          authenticated business.\n    GET    /suppliers/me/questions         List unanswered/answered\n                                          questions across the supplier\'s\n                                          own products.\n\n    POST   /products/{id}/views             Record a product_views event\n                                          (business only; typically fired\n                                          automatically on product detail\n                                          view, not a user-initiated\n                                          action).\n    GET    /businesses/me/recently-viewed  List recently viewed products\n                                          (derived from product_views).\n\n    POST   /saved-products                 Save a product\n                                          (saved_products entry, business\n                                          only).\n    DELETE /saved-products/{product_id}    Remove a saved product.\n    GET    /saved-products                 List the authenticated\n                                          business\'s saved products.\n\n    POST   /saved-suppliers                Follow/save a supplier\n                                          (saved_suppliers entry, business\n                                          only). This is the primary\n                                          "save supplier" action used by\n                                          the product UI (Document 04,\n                                          Section 4.4).\n    DELETE /saved-suppliers/{supplier_id}  Unfollow/remove a saved\n                                          supplier.\n    GET    /saved-suppliers                List the authenticated\n                                          business\'s saved/followed\n                                          suppliers.\n\n================================================================================\n5.5 TRUST DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: business_supplier_relationships, relationship_events,\ntrust_signals, business_health_scores, supplier_reputation_scores,\ntrust_score_history.\n\nEndpoints in this domain are predominantly read-only from the client\'s\nperspective; writes are performed by internal recalculation jobs triggered\nby Marketplace Domain events (Document 06, Sections 15–17), not by direct\nclient requests.\n\n    GET    /businesses/me/relationships     List the authenticated\n                                           business\'s business_supplier_\n                                           relationships (i.e. suppliers\n                                           they have an established\n                                           relationship with).\n    GET    /businesses/me/relationships/{supplier_id}\n                                           Get relationship detail with a\n                                           specific supplier, including\n                                           relationship_health_score and\n                                           recent relationship_events.\n    GET    /suppliers/me/relationships      List the authenticated\n                                           supplier\'s relationships with\n                                           businesses (subject to Business\n                                           Privacy rules — Document 09 —\n                                           when rendering customer\n                                           identity).\n\n    GET    /businesses/me/health-score       Get current\n                                           business_health_scores entry\n                                           for the authenticated business.\n    GET    /businesses/me/health-score/history\n                                           Get trust_score_history for the\n                                           authenticated business (trend\n                                           display, e.g. "Business Growth\n                                           +37%").\n    GET    /suppliers/me/reputation-score    Get current\n                                           supplier_reputation_scores entry\n                                           for the authenticated supplier.\n    GET    /suppliers/me/reputation-score/history\n                                           Get trust_score_history for the\n                                           authenticated supplier.\n\n    Internal/system-only (not exposed to mobile clients):\n    POST   /internal/trust/recalculate      Trigger recalculation of\n                                           trust_signals,\n                                           business_health_scores, and/or\n                                           supplier_reputation_scores for a\n                                           given owner, invoked by\n                                           background workers on the\n                                           trigger events defined in\n                                           Document 06.\n\n================================================================================\n5.6 VERIFICATION DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: verification_requests, verification_documents,\nverification_history.\n\n    POST   /verification/requests           Submit a new\n                                           verification_requests entry\n                                           (business or supplier), with\n                                           accompanying\n                                           verification_documents.\n    GET    /verification/requests/mine       List the authenticated\n                                           account\'s own verification\n                                           requests and current status.\n    GET    /verification/requests/{id}       Get a specific verification\n                                           request, including its\n                                           verification_documents and\n                                           verification_history (owner-\n                                           restricted, or admin).\n    POST   /verification/requests/{id}/documents\n                                           Add an additional supporting\n                                           document to an existing\n                                           request.\n\n    Admin-only (future role, Document 01 Section 9.3):\n    PUT    /admin/verification/requests/{id}/review\n                                           Approve or reject a\n                                           verification_requests entry;\n                                           writes a verification_history\n                                           entry and updates the\n                                           denormalised is_verified flag\n                                           on the owning business/supplier.\n    GET    /admin/verification/requests      List/queue verification\n                                           requests pending review.\n\n================================================================================\n5.7 PLATFORM DOMAIN — ENDPOINTS\n================================================================================\n\nBacking tables: notifications, notification_preferences, audit_logs,\nsystem_settings, lookup_categories, provinces, cities.\n\n    GET    /notifications                  List notifications for the\n                                          authenticated user, paginated,\n                                          filterable by read/unread.\n    PUT    /notifications/{id}/read        Mark a notification as read.\n    PUT    /notifications/read-all         Mark all notifications as read.\n    GET    /notifications/unread-count     Get unread notification count\n                                          (for badge display).\n\n    GET    /notification-preferences        Get the authenticated user\'s\n                                          notification_preferences.\n    PUT    /notification-preferences        Update notification\n                                          preferences (per type/channel).\n\n    GET    /categories                     List lookup_categories,\n                                          filterable by applies_to\n                                          (business, supplier, product).\n    GET    /provinces                      List provinces.\n    GET    /provinces/{id}/cities           List cities within a province.\n\n    Admin-only (future role, Document 01 Section 9.3):\n    GET    /admin/audit-logs                List audit_logs, filterable by\n                                          user, entity_type, and date\n                                          range.\n    GET    /admin/system-settings            List system_settings.\n    PUT    /admin/system-settings/{key}      Update a system_settings\n                                          value.\n\n================================================================================\n6. FUTURE ENDPOINTS (PLACEHOLDER — NOT IMPLEMENTED IN PHASE 1)\n================================================================================\n\nAnticipated to form a new "Financial Domain" API grouping (5.8) alongside\nPhase 2/3 of the roadmap (Document 08), backed by the future-scoped tables\nin Document 04, Section 6.\n\n6.1 Wallet (Phase 2)\n    GET /wallet/me, POST /wallet/topup, GET /wallet/transactions\n\n6.2 Credit (Phase 3)\n    POST /credit/apply, GET /credit/status, GET /credit/offers\n\n6.3 AI / Recommendations (Phase 2+)\n    GET /ai/recommendations/products, GET /ai/recommendations/suppliers,\n    GET /ai/business-health-insights\n\nThese are documented here only to ensure the current API versioning and\nrouting structure (/api/v1/...) can accommodate them without breaking\nexisting consumers, per the Scalable Architecture principle (Document 01).\n\n================================================================================\n7. ROLE-BASED ACCESS SUMMARY\n================================================================================\n\n    Business-only endpoints: place/cancel orders, submit business\n    questions, save products/suppliers, manage own business profile,\n    addresses, documents, and settings.\n\n    Supplier-only endpoints: manage products (and product images),\n    delivery regions, business hours, accept/reject/complete orders,\n    respond to business questions, publish supplier updates.\n\n    Shared/public endpoints: view supplier profiles and products, view\n    business questions threads, view categories/provinces/cities.\n\n    Admin-only endpoints (future role): review verification requests,\n    manage roles/permissions, view audit logs, manage system settings.\n\n    All write operations validate resource ownership (a supplier cannot\n    modify another supplier\'s product; a business cannot cancel another\n    business\'s order) at the application layer, using the roles/\n    permissions structure (Document 04, Section 4.1) in addition to\n    authentication.\n',
    '06_BUSINESS_RULES_AND_WORKFLOWS.txt': '================================================================================\n                            TRU CONNECT\n              BUSINESS RULES AND WORKFLOWS\n                          Document 06 ⭐\n================================================================================\n\nVersion: 1.0\nRelated Documents: 05_BACKEND_API_SPECIFICATION.txt,\n                    07_DATA_AND_TRUST_ENGINE.txt\n\nPurpose: Document every business workflow governing TRU Connect, so that\nengineering, QA, and product teams share a single definition of expected\nsystem behaviour.\n\n================================================================================\n1. BUSINESS REGISTRATION\n================================================================================\n\n    1. User selects "For Businesses" on the landing screen.\n    2. User registers via email/password or Continue with Google.\n    3. User provides basic business details: business name, category,\n       location, contact number.\n    4. Account is created with role = business, is_verified = false.\n    5. User lands on the Business Home Dashboard.\n    6. A Digital Business Profile record is initialised (zero-state) for\n       the new business, ready to accrue data as described in Document 07.\n\nRules:\n    - A single email or Google account may only be associated with one\n      role (business or supplier). Switching roles requires a separate\n      account.\n    - Business registration does not require verification documents to be\n      submitted immediately; verification may be completed at any point\n      but certain actions (see Section 3) require it.\n\n================================================================================\n2. SUPPLIER REGISTRATION\n================================================================================\n\n    1. User selects "For Suppliers" on the landing screen.\n    2. User registers via email/password or Continue with Google.\n    3. User provides supplier details: supplier name, category, regions\n       served, contact number.\n    4. Account is created with role = supplier, is_verified = false.\n    5. User lands on the Supplier Home Dashboard.\n    6. A Supplier Profile record is initialised (zero-state).\n\nRules:\n    - A supplier cannot publish products until at least basic profile\n      information is complete (name, category, regions served).\n    - As with businesses, verification is not mandatory at registration\n      but gates certain higher-trust actions.\n\n================================================================================\n3. VERIFICATION\n================================================================================\n\n    1. User (business or supplier) submits verification documents via\n       POST /verification/submit.\n    2. Verification record is created with status = pending.\n    3. Verification is reviewed (Phase 1: manual review process; future\n       phases may introduce automated verification checks).\n    4. On approval: status = approved, and is_verified flag on the parent\n       Business/Supplier record is set to true. A Verification Badge\n       becomes visible on the account\'s public profile and cards.\n    5. On rejection: status = rejected, with reviewer notes retained\n       internally (never shown to the end user beyond a generic\n       "additional information required" message).\n\nRules:\n    - Suppliers must reach approved verification status before their\n      profile appears in "Featured Suppliers" listings (though they may\n      still appear in general search/discovery as unverified).\n    - Businesses are not required to verify to place orders in Phase 1,\n      but verification directly contributes to a higher Business Health\n      Score (Document 07) and may become a requirement for future credit\n      products (Phase 3).\n\n================================================================================\n4. PRODUCT LISTING (SUPPLIER)\n================================================================================\n\n    1. Supplier creates a product: name, category, description, price,\n       unit, minimum order quantity, stock status.\n    2. Product is created with is_published = true by default (or false, if\n       the supplier chooses to save as draft).\n    3. Published products become visible in business-facing search,\n       category browsing, and recommendations.\n    4. Supplier may update stock status at any time (in_stock, low_stock,\n       out_of_stock); out_of_stock products remain visible but are marked\n       accordingly and excluded from "Popular Products" ranking.\n\nRules:\n    - A product must belong to exactly one category.\n    - Deleting a product does not hard-delete historical Order Items\n      referencing it; the product record is soft-deleted / unpublished\n      instead, preserving order history integrity.\n\n================================================================================\n5. SEARCHING SUPPLIERS (BUSINESS)\n================================================================================\n\n    1. Business enters a keyword and/or selects a category/location filter\n       in the Suppliers tab.\n    2. System returns matching suppliers, ranked by a combination of\n       relevance, verification status, distance, and relationship\n       signals (e.g. previously ordered-from suppliers may rank higher\n       for that specific business — see Document 07).\n    3. Business may further filter by "Verified only."\n\nRules:\n    - Search and view events are logged as business activity, feeding the\n      Digital Business Profile and recommendation systems (Document 07),\n      but this is never surfaced to the user as a step in a "profile\n      building" process — it is purely a background effect of normal use.\n\n================================================================================\n6. VIEWING PRODUCTS\n================================================================================\n\n    1. Business opens a supplier profile or search result and selects a\n       product.\n    2. Product Detail screen loads, including price, availability,\n       minimum order quantity, and the attached Business Questions thread.\n    3. View event is logged (contributes to "Recently Viewed" and supplier/\n       product popularity signals).\n\n================================================================================\n7. BUSINESS QUESTIONS (ASK)\n================================================================================\n\n    1. Business submits a question beneath a product via the\n       BusinessQuestionThread component.\n    2. Question is stored, associated with the product and the asking\n       business, and categorised (availability, delivery, pricing, bulk\n       order, packaging, specifications, general).\n    3. Supplier receives a notification of a new, unanswered question.\n    4. Question and any future response remain permanently attached to the\n       product, visible to all future viewers (see Document 09 rationale).\n\nRules:\n    - A business may ask multiple questions on the same product.\n    - Questions are not private messages; they are treated as shared,\n      public product knowledge by design.\n\n================================================================================\n8. SUPPLIER RESPONSES\n================================================================================\n\n    1. Supplier views unanswered questions across their product catalogue\n       (aggregated view) or on an individual product.\n    2. Supplier submits a response.\n    3. Responding business (and all future viewers of the product) can see\n       the response attached beneath the original question.\n    4. Response event updates the supplier\'s average_response_time_minutes\n       and response_rate_percentage (Document 07).\n\nRules:\n    - Only the supplier who owns the product may respond to a question on\n      that product.\n    - A question may only have one official Supplier Response (edits to an\n      existing response are allowed; a second independent response is\n      not, to avoid conflicting or duplicated answers).\n\n================================================================================\n9. BOOKMARK SUPPLIER\n================================================================================\n\n    1. Business selects "Save" or "Follow" on a supplier profile or\n       Supplier Card.\n    2. A Bookmark record is created linking the business and supplier.\n    3. Bookmarked suppliers appear in the "Saved Suppliers" list and the\n       business begins receiving notifications for that supplier\'s future\n       Business Updates.\n\nRules:\n    - Bookmarking is a one-directional signal; it does not require\n      supplier approval and does not notify the supplier.\n\n================================================================================\n10. PLACE ORDER\n================================================================================\n\n    1. Business adds one or more products (with quantities, respecting\n       each product\'s minimum order quantity) from a single supplier to an\n       order.\n    2. Business confirms delivery address and reviews order total.\n    3. Business submits the order (POST /orders); order is created with\n       status = pending.\n    4. Supplier receives a notification of a new incoming order.\n\nRules:\n    - An order may only contain products from a single supplier (no\n      cross-supplier carts in Phase 1); ordering from multiple suppliers\n      requires separate orders.\n    - Order total is calculated at submission time using each product\'s\n      current price and any applicable bulk pricing rules; this price is\n      locked into the Order Item (unit_price_at_order_time) regardless of\n      later price changes.\n\n================================================================================\n11. ACCEPT ORDER\n================================================================================\n\n    1. Supplier reviews an incoming pending order.\n    2. Supplier accepts the order (PUT /orders/{id}/accept).\n    3. Order status transitions to accepted; accepted_at timestamp is\n       recorded.\n    4. Business receives a notification of acceptance.\n    5. Order proceeds to in_fulfilment status once the supplier begins\n       preparing/dispatching the order (implementation may combine this\n       step with acceptance depending on supplier workflow needs).\n\n================================================================================\n12. REJECT ORDER\n================================================================================\n\n    1. Supplier declines an incoming pending order, providing a reason\n       (e.g. out of stock, outside delivery area, minimum not met).\n    2. Order status transitions to rejected.\n    3. Business receives a notification including the rejection reason.\n\nRules:\n    - A rejected order does not count against the business\'s order\n      history in a negative way; it is excluded from repeat-order and\n      trust calculations for that business (Document 07), since the\n      failure to fulfil originates with the supplier\'s decision.\n    - Frequent rejections by a supplier negatively affect that supplier\'s\n      response_rate_percentage and overall Supplier Profile.\n\n================================================================================\n13. COMPLETE ORDER\n================================================================================\n\n    1. Supplier fulfils and delivers the order.\n    2. Order status transitions to completed, either via explicit supplier\n       action or system-triggered confirmation (e.g. delivery tracking\n       reaching a "delivered" state, in later phases with more advanced\n       logistics integration).\n    3. completed_at timestamp is recorded.\n    4. An Invoice becomes available for the order.\n    5. Completion triggers recalculation of both the business\'s Digital\n       Business Profile and the supplier\'s Supplier Profile statistics\n       (Document 07).\n\n================================================================================\n14. ORDER HISTORY\n================================================================================\n\n    - Both business and supplier can view historical orders, filterable by\n      status (current, pending, completed, cancelled/rejected).\n    - Order history is immutable once an order reaches a terminal state\n      (completed, cancelled, rejected); only delivery tracking metadata may\n      continue to update post-completion for record-keeping purposes.\n\n================================================================================\n15. BUSINESS PROFILE UPDATES (DIGITAL BUSINESS PROFILE RECALCULATION)\n================================================================================\n\nTrigger events that cause recalculation of a business\'s Digital Business\nProfile:\n    - Order placed\n    - Order completed\n    - Order cancelled/rejected\n    - New supplier relationship established (first order with a new\n      supplier)\n    - Verification status change\n\nRecalculated fields: orders_count, suppliers_count, average_order_value,\nlargest_order_value, repeat_supplier_rate, average_payment_time_days,\nbusiness_growth_percentage, risk_level.\n\nFull methodology is defined in Document 07.\n\n================================================================================\n16. SUPPLIER STATISTICS (SUPPLIER PROFILE RECALCULATION)\n================================================================================\n\nTrigger events:\n    - Order received / accepted / rejected / completed\n    - Business Question response submitted\n    - New verification status change\n\nRecalculated fields: businesses_served_count, orders_completed_count,\nrepeat_customer_rate, average_response_time_minutes,\nresponse_rate_percentage.\n\n================================================================================\n17. TRUST UPDATES\n================================================================================\n\n    1. Any of the trigger events in Sections 15–16 causes an asynchronous\n       recalculation job to run (rather than blocking the user-facing\n       request/response cycle).\n    2. Updated profile values are persisted to the Business Profile /\n       Supplier Profile tables.\n    3. Relationship-level statistics (Document 04, Section 16) are updated\n       for the specific business-supplier pair involved.\n    4. See Document 07 for the full set of signals feeding these\n       calculations and their intended future use in risk assessment.\n\n================================================================================\n18. NOTIFICATION DELIVERY RULES\n================================================================================\n\n    - Order-related notifications (placed, accepted, rejected, completed)\n      are delivered immediately/synchronously with the triggering event.\n    - Business Question response notifications are delivered immediately\n      to the original asking business.\n    - Business Update notifications are delivered to all businesses that\n      have bookmarked/followed the publishing supplier.\n    - Verification status change notifications are delivered immediately\n      upon review completion.\n\n================================================================================\n19. ACCOUNT & DATA INTEGRITY RULES\n================================================================================\n\n    - Soft-delete is used for Businesses, Suppliers, Orders, and\n      Verification Records to preserve historical trust data (Document 04,\n      Section 19).\n    - A business or supplier may deactivate their own account; deactivation\n      hides the profile from discovery but preserves historical order and\n      relationship data for trust-engine integrity and any pending legal/\n      financial record-keeping requirements.\n',
    '07_DATA_AND_TRUST_ENGINE.txt': '================================================================================\n                            TRU CONNECT\n                    DATA AND TRUST ENGINE\n                          Document 07 ⭐\n                    (Competitive Advantage)\n================================================================================\n\nVersion: 1.0\nRelated Documents: 04_DATABASE_DESIGN.txt, 06_BUSINESS_RULES_AND_WORKFLOWS.txt,\n                    09_ECOSYSTEM_STRATEGY.txt\n\nPurpose: Document how ordinary business activity on TRU Connect is quietly\ntransformed into structured, trusted business intelligence — the platform\'s\ncore long-term asset.\n\n================================================================================\n1. OVERVIEW\n================================================================================\n\nEvery interaction on TRU Connect — a search, a question, an order, a\ndelivery, a repeat purchase — is treated as a signal. These signals are\ncontinuously aggregated into two outward-facing profiles:\n\n    - The Digital Business Profile (for businesses)\n    - The Supplier Profile / Business Performance profile (for suppliers)\n\nNeither profile is manually completed by the user. Both are entirely\nderived from observed platform activity, recalculated asynchronously as\ndescribed in Document 06, Sections 15–17.\n\n================================================================================\n2. DIGITAL BUSINESS PROFILE\n================================================================================\n\nDisplayed fields and their derivation:\n\n    Business Since           — registered_since date from Businesses table.\n    Orders                    — count of completed orders (rejected/\n                                cancelled orders excluded).\n    Suppliers                — count of distinct suppliers with at least\n                                one completed order (i.e. established\n                                Relationships, Document 04 Section 16).\n    Average Order            — mean total_amount across completed orders.\n    Largest Order             — maximum total_amount across completed\n                                orders.\n    Repeat Supplier Rate      — percentage of suppliers with more than one\n                                completed order, out of total suppliers\n                                engaged.\n    Average Payment Time      — mean number of days between order\n                                acceptance and payment confirmation (Phase\n                                1: proxied by order completion time in the\n                                absence of a payments module; refined once\n                                Phase 2 payments/wallet data is available).\n    Business Growth           — percentage change in order volume and/or\n                                value over a rolling period (e.g. quarter-\n                                over-quarter).\n    Risk Level                — a categorical (low/medium/high) output\n                                derived from the signals in Section 4,\n                                described further in Section 6.\n\n================================================================================\n3. SUPPLIER RELATIONSHIPS & RELATIONSHIP HEALTH\n================================================================================\n\nEach distinct business-supplier pair accrues its own relationship record\n(Document 04, Section 16), tracking:\n\n    - first_interaction_at / last_interaction_at\n    - total_orders / total_order_value\n    - relationship_health_score\n\nRelationship Health Score is a composite signal reflecting:\n    - Frequency of orders between the pair.\n    - Recency of the last interaction (a relationship that has gone quiet\n      contributes less to ongoing trust signals than an active one).\n    - Order completion rate within the pair (completed vs. cancelled/\n      rejected).\n    - Responsiveness of Business Questions exchanged between the pair, if\n      any.\n\nRelationships are the fundamental unit of trust in TRU Connect, distinct\nfrom and more informative than isolated transactions (see Document 09,\n"Why Relationships Matter").\n\n================================================================================\n4. REPEAT ORDERS\n================================================================================\n\nRepeat orders — multiple completed orders between the same business and\nsupplier — are weighted more heavily than first-time orders in trust\ncalculations, because they represent a demonstrated, ongoing willingness to\ntransact again, which is a stronger signal of satisfaction and reliability\nthan a single transaction.\n\nRepeat Supplier Rate (Business Profile) and Repeat Customer Rate (Supplier\nProfile) are both first-class, prominently displayed metrics for this\nreason.\n\n================================================================================\n5. PRODUCT VIEWS\n================================================================================\n\nProduct view events (Document 06, Section 6) contribute to:\n    - "Recently Viewed" personalisation for the viewing business.\n    - Product and supplier popularity ranking (aggregate, anonymised).\n    - Early-stage interest signals that may precede an order (used for\n      future recommendation-engine training data, Phase 2+).\n\nProduct views alone do not materially affect a business\'s Digital Business\nProfile risk/trust fields; they are primarily a discovery and\nrecommendation signal, not a creditworthiness signal.\n\n================================================================================\n6. BUSINESS QUESTIONS & SUPPLIER RESPONSES AS TRUST SIGNALS\n================================================================================\n\nBusiness Questions and Supplier Responses (see Document 09 for the product\nrationale) generate two distinct signal streams:\n\n6.1 For the Business (asker)\n    - Engagement signal: businesses that actively ask questions before\n      ordering demonstrate deliberate, considered purchasing behaviour, a\n      mild positive input to overall engagement scoring.\n\n6.2 For the Supplier (responder)\n    - average_response_time_minutes — time between question submission\n      and response submission.\n    - response_rate_percentage — proportion of received questions that\n      receive an official response at all.\n    - These two metrics feed directly into the Supplier Profile and are\n      surfaced publicly, since responsiveness is one of the strongest\n      available proxies for supplier reliability in the absence of\n      traditional reviews (Document 09).\n\n================================================================================\n7. ORDER BEHAVIOUR\n================================================================================\n\nOrder-level behavioural signals tracked per business:\n    - Order frequency and volume trend over time.\n    - Distribution of orders across distinct suppliers (concentration vs.\n      diversification of sourcing).\n    - Cancellation rate (business-initiated cancellations, distinct from\n      supplier rejections).\n    - Value consistency (variance in order size over time).\n\nOrder-level behavioural signals tracked per supplier:\n    - Acceptance rate of incoming orders.\n    - Fulfilment completion rate.\n    - Time from acceptance to completion.\n\n================================================================================\n8. RISK SIGNALS & TRUST SIGNALS\n================================================================================\n\nThe platform distinguishes conceptually between:\n\n    Trust Signals — evidence of positive, reliable commercial behaviour\n    (repeat orders, verification, responsiveness, consistent payment\n    behaviour, longevity on the platform).\n\n    Risk Signals — evidence that may indicate unreliability or elevated\n    risk (frequent cancellations, disputed orders, lapsed verification,\n    inconsistent or declining activity, unusually rapid changes in order\n    volume that do not correspond to a verified business event).\n\nBoth signal types feed into the Risk Level field on the Digital Business\nProfile and, in future phases, into more formal risk-scoring models used\nfor credit and trade finance decisioning (Phase 3, see Document 08).\n\n================================================================================\n9. AI FEATURE GENERATION (FORWARD-LOOKING)\n================================================================================\n\nAs platform activity volume grows, raw signals described above become\ninputs (features) for machine learning models supporting:\n    - Supplier and product recommendations personalised to a business\'s\n      order history and category.\n    - Early identification of at-risk relationships (e.g. a previously\n      active relationship going quiet) for potential re-engagement\n      prompts.\n    - Business Health Score refinement beyond the initial rule-based\n      calculation described in this document.\n    - Future credit risk models (Phase 3), trained on the accumulated\n      Trust and Risk Signal history described above.\n\nPhase 1 implementation should favour transparent, rule-based calculations\n(as described in Sections 2–8) over opaque ML models, both for simplicity\nof initial build and for explainability of any early risk indicators shown\nto users or, later, to financial partners.\n\n================================================================================\n10. BUSINESS HEALTH SCORE\n================================================================================\n\nThe Business Health Score (referenced in the Digital Business Profile as\n"Business Growth" and "Risk Level," and expandable in future UI iterations\ninto a single composite score) is calculated from a weighted combination\nof:\n\n    - Order volume and value trend (recency-weighted)\n    - Repeat Supplier Rate\n    - Verification status\n    - Average Payment Time\n    - Relationship Health Scores across all supplier relationships\n    - Absence of negative Risk Signals (Section 8)\n\nThe precise weighting formula should be treated as a configurable,\nversioned parameter set (not hard-coded), since it is expected to be\nrefined as more platform data becomes available and as Phase 3 credit\nproducts introduce more rigorous validation requirements.\n\n================================================================================\n11. SUPPLIER REPUTATION\n================================================================================\n\nMirroring the Business Health Score, supplier reputation is derived from:\n    - Businesses Served (count of distinct businesses with completed\n      orders)\n    - Orders Completed\n    - Repeat Customer Rate\n    - Average Response Time / Response Rate\n    - Verification Status\n    - Active Since (longevity)\n\nThis composite reputation is what replaces traditional star ratings across\nthe platform (see Document 09 for full rationale), and is displayed via the\nBusinessPerformanceCard component (Document 03).\n\n================================================================================\n12. COMMERCIAL RELATIONSHIPS AS THE UNIT OF TRUST\n================================================================================\n\nWhere a traditional marketplace treats each transaction as an independent\nevent, TRU Connect\'s trust engine treats the business-supplier Relationship\n(Document 04, Section 16) as the primary unit of analysis. A business with\nfewer, deeper supplier relationships may in some contexts present a\nstronger trust profile than one with many shallow, one-off transactions,\nbecause sustained relationships are harder to fabricate and more\npredictive of continued reliable behaviour.\n\n================================================================================\n13. FUTURE CREDIT READINESS\n================================================================================\n\n"Credit Readiness" is not a Phase 1 user-facing feature, but the trust\nengine described in this document is explicitly designed to produce the\ndata needed for it in Phase 3:\n\n    - A business or supplier is considered "credit-ready" in future\n      phases once their accumulated Trust Signals cross defined,\n      configurable thresholds (e.g. minimum order history length, minimum\n      verification status, minimum relationship health across suppliers).\n    - No business or supplier is ever required to manually assemble this\n      readiness; it is a natural, cumulative output of ordinary platform\n      use, consistent with the "Trust Before Lending" principle in\n      Document 00.\n    - When Phase 3 is reached, this document\'s signal set becomes the\n      direct input specification for underwriting model design, avoiding\n      the need to retrofit data collection after the fact.\n',
    '08_PRODUCT_ROADMAP.txt': '================================================================================\n                            TRU CONNECT\n                        PRODUCT ROADMAP\n                          Document 08\n================================================================================\n\nVersion: 1.0\nRelated Documents: 00_PROJECT_VISION.txt, 07_DATA_AND_TRUST_ENGINE.txt,\n                    09_ECOSYSTEM_STRATEGY.txt\n\nPurpose: Define the phased evolution of TRU Connect, ensuring each phase\nbuilds directly on the trust and data foundations established by the\nphases before it.\n\n================================================================================\nPHASE 1 — FOUNDATION: DISCOVERY, TRUST, AND ORDERING\n================================================================================\n\nObjective: Establish the core marketplace and the data foundations required\nfor every subsequent phase.\n\nScope:\n    - Business and Supplier registration and authentication (email/\n      password, Google).\n    - Supplier Discovery (search, categories, nearby, featured, popular\n      products, saved suppliers).\n    - Product Catalogue management (supplier-facing).\n    - Orders (placement, acceptance, rejection, completion, tracking,\n      invoices).\n    - Business Questions & Supplier Responses ("Business Conversations").\n    - Verification (business and supplier).\n    - Digital Business Profile and Supplier Profile (automatically\n      generated, rule-based, per Document 07).\n    - Business Updates (supplier announcements).\n    - Notifications.\n\nExit Criteria (informing readiness for Phase 2):\n    - Meaningful volume of verified businesses and suppliers actively\n      transacting.\n    - Sufficient repeat-order and relationship data flowing through the\n      trust engine to support meaningful Business Health Score and\n      Supplier Reputation calculations.\n    - Stable, well-tested core workflows (Document 06) with low order\n      dispute/rejection rates.\n\n================================================================================\nPHASE 2 — PAYMENTS, WALLET, AND INSIGHTS\n================================================================================\n\nObjective: Introduce financial transaction infrastructure and surface\nricher insights back to businesses and suppliers, without yet introducing\ncredit or lending.\n\nScope:\n    - Payments — in-app payment processing for orders, replacing or\n      supplementing existing offline payment methods.\n    - Wallet — a stored-value account for businesses and/or suppliers,\n      enabling faster transactions and providing a foundation for future\n      credit disbursement and repayment rails (Phase 3).\n    - Business Insights — business-facing analytics building on the\n      Digital Business Profile (e.g. spending trends, supplier\n      diversification, seasonal patterns).\n    - Supplier Analytics — supplier-facing analytics building on the\n      Supplier Profile (e.g. demand trends, customer retention patterns,\n      response-time benchmarking against category peers).\n\nDependencies on Phase 1:\n    - Wallet and Payments rely on the Orders and Relationship data\n      structures established in Phase 1 (Document 04).\n    - Average Payment Time (Document 07) becomes materially more accurate\n      once real payment timestamps are available via the Wallet/Payments\n      module, rather than being proxied by order completion time.\n\nExit Criteria:\n    - Reliable, audited payment and wallet transaction history.\n    - Adoption of in-app payments by a meaningful share of active\n      relationships, generating a genuine (not proxied) payment-behaviour\n      signal for the trust engine.\n\n================================================================================\nPHASE 3 — CREDIT, TRADE FINANCE, AND WORKING CAPITAL\n================================================================================\n\nObjective: Introduce financial products, underwritten using the trust and\npayment data accumulated in Phases 1 and 2.\n\nScope:\n    - Credit — short-term credit facilities for businesses (e.g. stock\n      financing) based on Business Health Score and order history.\n    - Trade Finance — financing instruments supporting larger or\n      recurring supplier transactions.\n    - Working Capital — working capital facilities for suppliers based on\n      their Supplier Reputation and completed-order history.\n    - Financial Products — packaging of the above into user-facing\n      offerings, potentially in partnership with external financial\n      institutions (anticipating Phase 4).\n\nDependencies on Phases 1–2:\n    - Underwriting models consume the Trust Signals, Risk Signals, and\n      Relationship Health data defined in Document 07, plus real payment\n      behaviour data from Phase 2.\n    - "Credit Readiness" thresholds (Document 07, Section 13) determine\n      initial eligibility, ensuring credit is only extended where\n      sufficient verified commercial history exists — consistent with the\n      "Trust Before Lending" principle (Document 00).\n\nExit Criteria:\n    - Defined, tested underwriting/risk model with acceptable performance\n      on historical platform data.\n    - Regulatory and compliance readiness for offering credit products in\n      relevant jurisdictions.\n    - Initial credit product performance (repayment rates) validating the\n      underlying trust engine\'s predictive value.\n\n================================================================================\nPHASE 4 — PARTNER APIS, FINANCIAL INSTITUTIONS, AND OPEN PLATFORM\n================================================================================\n\nObjective: Position TRU Connect as shared, open trust infrastructure\nconnecting the informal economy to the broader financial system.\n\nScope:\n    - Partner APIs — controlled, permissioned API access allowing external\n      partners to integrate with TRU Connect\'s business/supplier data\n      (subject to consent and privacy rules, Document 09).\n    - Financial Institutions — direct integrations enabling banks, lenders,\n      and insurers to originate products (credit, insurance, savings)\n      using TRU Connect\'s trust data, with TRU Connect / TruePoint acting\n      as the verified data and relationship layer rather than the sole\n      lender.\n    - Open Platform Expansion — potential extension of the ecosystem to\n      adjacent services (e.g. logistics partners, insurance providers)\n      built on the same trust infrastructure.\n\nDependencies on Phases 1–3:\n    - Requires a mature, well-validated trust engine (Document 07) and a\n      demonstrated track record of credit performance from Phase 3.\n    - Requires robust data governance, consent, and privacy\n      infrastructure to support external data sharing responsibly.\n\nExit Criteria:\n    - Signed institutional partnerships with clearly defined data-sharing\n      and revenue arrangements.\n    - Scalable, secure partner API infrastructure independently audited\n      for security and data protection compliance.\n\n================================================================================\nCROSS-PHASE ARCHITECTURAL COMMITMENTS\n================================================================================\n\nTo ensure each phase can be built without reworking earlier phases, the\nfollowing commitments apply from Phase 1 onward:\n\n    1. Database schema (Document 04) explicitly reserves entities/fields\n       for Wallet, Credit, and Risk Signal data, even though they are\n       unused until Phases 2–3.\n    2. API versioning (Document 05) uses a stable, versioned base path to\n       allow additive expansion without breaking existing mobile clients.\n    3. The trust engine (Document 07) is built on transparent, rule-based\n       calculations first, to keep early risk indicators explainable\n       before any machine-learning-based refinement is introduced.\n    4. Business Privacy and Supplier Visibility rules (Document 09) are\n       enforced from Phase 1 onward, anticipating the heightened data-\n       governance requirements of Phases 3–4.\n',
    '09_ECOSYSTEM_STRATEGY.txt': '================================================================================\n                            TRU CONNECT\n                     ECOSYSTEM STRATEGY\n                          Document 09 ⭐\n              Beyond a Marketplace — Building Trusted\n                    Business Infrastructure\n================================================================================\n\nVersion: 1.0\nRelated Documents: 00_PROJECT_VISION.txt, 01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt,\n                    07_DATA_AND_TRUST_ENGINE.txt, 08_PRODUCT_ROADMAP.txt\n\nPurpose: Explain why every feature in TRU Connect exists, ensuring future\ndevelopment stays aligned with the ecosystem vision rather than drifting\ntoward generic marketplace conventions.\n\n================================================================================\n1. CORE OBJECTIVE\n================================================================================\n\nTRU Connect is not designed to become another online marketplace.\n\nIts purpose is to help businesses discover trusted suppliers, build trusted\nbusiness relationships, and quietly create the business data needed to\nunlock future financial opportunities.\n\nBuying and selling products is only one feature of a much larger ecosystem.\nEvery feature decision in this document should be evaluated against this\nobjective before being adopted.\n\n================================================================================\n2. CORE PHILOSOPHY: RELATIONSHIPS OVER TRANSACTIONS\n================================================================================\n\nTraditional marketplaces focus on transactions. TRU Connect focuses on\nrelationships.\n\nEvery interaction between businesses and suppliers contributes to building\na trusted digital business ecosystem, not merely to closing a sale. This\nphilosophy shapes every decision documented below.\n\n================================================================================\n3. WHY BUSINESS QUESTIONS INSTEAD OF REVIEWS\n================================================================================\n\nInstead of traditional product reviews or private messaging, TRU Connect\nintroduces Business Conversations: businesses ask questions directly\nbeneath supplier products (availability, delivery locations and times,\nbulk pricing, minimum order quantities, packaging, specifications, general\nbusiness enquiries). Supplier responses remain attached to the product,\nso future businesses benefit from previously answered questions.\n\nWhy this matters:\n    - Star ratings are easily manipulated and rarely reflect real\n      commercial behaviour. A rating of "4.7 stars" tells a business\n      almost nothing actionable.\n    - Business Questions create transparency instead: businesses can see\n      exactly what was asked, how the supplier responded, and infer\n      delivery capability, pricing policy, service quality, and business\n      professionalism directly from real exchanges.\n    - Rather than isolated, one-off conversations, every discussion\n      becomes shared business knowledge — a growing Business Knowledge\n      Base per supplier (questions, responses, delivery/packaging/\n      availability/bulk-order/region information, effectively a living\n      FAQ), reducing repetitive enquiries and creating long-term value for\n      both suppliers and future customers.\n    - Trust becomes visible through communication rather than ratings\n      alone.\n\n================================================================================\n4. WHY SUPPLIER PROFILES ARE PUBLIC\n================================================================================\n\nSupplier profiles remain publicly visible, showing profile information,\nverification status, products, business information, Business Questions,\nBusiness Updates, and customer statistics.\n\nWhy this matters:\n    - Public visibility increases transparency and encourages trust — a\n      business considering a new supplier should be able to fully assess\n      that supplier\'s track record before ever placing an order.\n    - Suppliers benefit from public profiles as a discovery and reputation-\n      building channel, similar to a professional storefront, reinforcing\n      their standalone incentive to participate on the platform.\n\n================================================================================\n5. WHY BUSINESS PROFILES ARE PROTECTED\n================================================================================\n\nBusiness customers remain largely private. Rather than exposing detailed\nbusiness information, customer identities are limited to a generic\n"Verified Business" or a partially identified label such as "ABC Store\n(Verified)," without revealing unnecessary commercial information.\n\nWhy this matters:\n    - Protecting customer privacy helps maintain trust while reducing\n      unnecessary competitive exposure — a small business should not have\n      to worry that its sourcing relationships or order volumes are\n      visible to competitors.\n    - This asymmetry (public suppliers, private businesses) is\n      intentional: suppliers are B2B storefronts seeking visibility;\n      businesses are the platform\'s primary users seeking protection and\n      utility, not exposure.\n\n================================================================================\n6. WHY RELATIONSHIPS MATTER\n================================================================================\n\nA specific, ongoing relationship between one business and one supplier\n(Document 04, Section 16; Document 07, Section 3) is treated as the\nfundamental unit of trust on TRU Connect — more informative than any single\ntransaction.\n\nWhy this matters:\n    - Relationships are harder to fabricate than isolated transactions and\n      are far more predictive of continued reliable behaviour.\n    - A business with deep, sustained relationships with a small number of\n      suppliers may represent a stronger trust profile than one with many\n      shallow, one-off purchases.\n    - This is why Relationship Health Score, Repeat Supplier Rate, and\n      Repeat Customer Rate are first-class, prominently displayed metrics\n      throughout the product (Documents 03 and 07), rather than secondary\n      statistics.\n\n================================================================================\n7. WHY REPEAT ORDERS MATTER\n================================================================================\n\nRepeat orders between the same business-supplier pair are weighted more\nheavily than first-time orders in all trust calculations (Document 07,\nSection 4).\n\nWhy this matters:\n    - A business that orders from the same supplier repeatedly is\n      demonstrating sustained satisfaction and reliability, a far stronger\n      signal than a single completed transaction.\n    - Repeat behaviour is also difficult to fake at scale, making it a\n      valuable, resilient signal for future risk and credit models\n      (Phase 3, Document 08).\n\n================================================================================\n8. WHY BUSINESS DATA MATTERS\n================================================================================\n\nEvery activity performed within TRU Connect — searching, viewing profiles\nand products, asking questions, receiving responses, bookmarking,\nfollowing, receiving enquiries, quotations, placing and completing orders,\nrepeat purchases, delivery performance, payment behaviour, product\nengagement, and verification — contributes to a richer digital business\nprofile.\n\nNone of these are "just marketplace features." Each interaction represents\nverified commercial behaviour, and collectively they form the foundation\nfor future business insights, AI-powered recommendations, credit risk\nassessment, supplier financing, trade credit, working capital, and\nfinancial partnerships (Document 08, Phases 2–4).\n\nBusinesses are never required to manually build their financial profile.\nIt grows naturally through everyday business activity — this is the direct\nproduct expression of the "invisible data collection" principle in\nDocument 00.\n\n================================================================================\n9. HOW TRUST IS BUILT\n================================================================================\n\nTrust on TRU Connect accumulates through a layered process:\n\n    1. Verification establishes a baseline identity trust signal.\n    2. Ordinary activity (search, viewing, questions) establishes early\n       engagement signals.\n    3. Completed orders establish transactional trust.\n    4. Repeat orders and sustained relationships establish durable,\n       high-confidence trust.\n    5. Consistent payment behaviour and low dispute/cancellation rates\n       reinforce and protect that trust over time.\n\nThis layered accumulation (detailed technically in Document 07) is what\nallows TRU Connect to eventually support credit decisioning without relying\non traditional collateral, paperwork, or credit bureau history that\nexcludes informal businesses today.\n\n================================================================================\n10. HOW COMMERCIAL RELATIONSHIPS BECOME BUSINESS INTELLIGENCE\n================================================================================\n\nThe Data and Trust Engine (Document 07) systematically converts the\nday-to-day commercial relationships described above into structured,\nqueryable business intelligence: the Digital Business Profile, the\nSupplier Profile, Relationship Health Scores, and — eventually — Business\nHealth Scores and formal risk models.\n\nThis is the mechanism by which "relationships" (a qualitative, human\nconcept) become "business intelligence" (a quantitative, systematic asset)\nwithout requiring the business or supplier to do anything beyond using the\nplatform as intended.\n\n================================================================================\n11. HOW BUSINESS ACTIVITY CREATES FINANCIAL READINESS\n================================================================================\n\nAs described in Document 07, Section 13, "Credit Readiness" is a\ncumulative output of ordinary platform activity crossing defined,\nconfigurable thresholds — not a separate application process.\n\nThis ensures the platform\'s financial products (Phase 3, Document 08) are\navailable first to those businesses and suppliers who have already\ndemonstrated reliability through real behaviour, directly operationalising\nthe "Trust Before Lending" principle from Document 00.\n\n================================================================================\n12. HOW TRU CONNECT EVOLVES INTO DIGITAL INFRASTRUCTURE\n================================================================================\n\nAs adoption grows, the accumulated network of verified businesses,\nverified suppliers, sustained relationships, and behavioural data\n(Document 07) evolves TRU Connect from a single application into shared\ninfrastructure: a trust and data layer that other participants — financial\ninstitutions, logistics partners, insurers — can eventually build upon via\nPartner APIs (Phase 4, Document 08).\n\n================================================================================\n13. HOW TRUEPOINT GAINS COMPETITIVE ADVANTAGE\n================================================================================\n\nTruePoint\'s competitive advantage does not come from being a marketplace\nwith more listings or lower prices than competitors. It comes from owning\na unique, defensible asset: a growing base of verified, trusted commercial\nrelationships and behavioural data that is extremely difficult for a\ngeneric marketplace to replicate after the fact, because it can only be\nbuilt through sustained real usage over time.\n\n================================================================================\n14. THE TRUEPOINT DIFFERENCE (SUMMARY COMPARISON)\n================================================================================\n\n    Traditional Marketplace\n        Goal:            Facilitate buying and selling.\n        Primary Asset:   Products.\n        Primary Metric:  Transactions.\n\n    TRU Connect Ecosystem\n        Goal:            Build trusted business relationships and digital\n                         business infrastructure.\n        Primary Asset:   Trusted commercial data.\n        Primary Metric:  Business relationships, verified activity, and\n                         long-term trust.\n\n================================================================================\n15. GUIDING PRINCIPLE\n================================================================================\n\nEvery search. Every enquiry. Every supplier relationship. Every order.\nEvery business conversation. Every repeat purchase. Every verified\ninteraction.\n\nQuietly builds the trusted digital business ecosystem that powers the\nfuture of TruePoint.\n\nAny proposed feature for TRU Connect should be evaluated against this\nprinciple: does it deepen a genuine business-supplier relationship and\ncontribute honestly to trusted commercial data, or does it merely optimise\nfor a one-off transaction? Features that serve the former should be\nprioritised; features that only serve the latter should be reconsidered.\n',
}



# ==============================================================================
# PATH CONSTANTS
# ==============================================================================

MOBILE_REL = os.path.join("frontend", "mobile")

ROOT_PLACEHOLDER_DIRS = [
    "backend",
    "database",
    "deployment",
    os.path.join("frontend", "web"),
    "scripts",
]

ROOT_README_CONTENT = """# TRU Connect

Monorepo root for the TRU Connect platform (mobile app, backend, database,
deployment, and documentation).

## Structure

```
TRU_Connect/
|-- backend/       Flask backend (Phase 2+, see docs/05_BACKEND_API_SPECIFICATION.txt)
|-- database/      PostgreSQL schema/migrations (see docs/04_DATABASE_DESIGN.txt)
|-- deployment/     Infrastructure & deployment configuration
|-- docs/          TRU Connect source-of-truth documentation (00-09)
|-- frontend/
|   |-- mobile/    Expo React Native application (current phase)
|   `-- web/       Future web application
`-- scripts/       Shared tooling scripts
```

## Documentation

Start with `docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt` -- the master
product specification and single source of truth for the whole platform.

## Current Phase

Phase 1: Authentication, Onboarding, Business Registration, Supplier
Registration, OTP Verification, Business Profile Wizard, Dashboard
Foundation. See `docs/08_PRODUCT_ROADMAP.txt` for the full roadmap.
"""


# ==============================================================================
# SDK 54 DEPENDENCY BASELINE
# ==============================================================================
# NOTE: Expo's dependency graph moves quickly between SDK releases. These
# versions are a reasonable SDK 54 baseline, but you should run
# `npx expo install --fix` immediately after this script runs -- it will
# correct any dependency that has since drifted from what SDK 54 expects,
# without needing this script to guess perfectly.

REQUIRED_DEPENDENCIES = {
    "expo": "~54.0.0",
    "expo-router": "~6.0.0",
    "expo-secure-store": "~15.0.0",
    "expo-linear-gradient": "~15.0.0",
    "expo-constants": "~18.0.0",
    "expo-status-bar": "~3.0.0",
    "expo-linking": "~8.0.0",
    "react": "19.1.0",
    "react-native": "0.81.4",
    "react-native-paper": "^5.12.3",
    "react-native-safe-area-context": "~5.6.0",
    "react-native-screens": "~4.16.0",
    "react-native-reanimated": "~4.1.0",
    "react-native-worklets": "~0.7.0",
    "react-native-gesture-handler": "~2.28.0",
    "react-native-svg": "~15.12.0",
    "react-native-pager-view": "~6.9.1",
    "lucide-react-native": "^0.469.0",
    "react-hook-form": "^7.51.5",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.8",
    "@tanstack/react-query": "^5.59.0",
    "axios": "^1.7.7",
    "zustand": "^4.5.5",
    "@react-native-async-storage/async-storage": "2.1.0",
}

REQUIRED_DEV_DEPENDENCIES = {
    "typescript": "~5.9.2",
    "@types/react": "~19.1.0",
    "babel-preset-expo": "~13.0.0",
}

REQUIRED_SCRIPTS = {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "typecheck": "tsc --noEmit",
}

REQUIRED_GITIGNORE_LINES = [
    "node_modules/",
    ".expo/",
    "dist/",
    "web-build/",
    "*.orig.*",
    ".env",
    ".DS_Store",
    "expo-env.d.ts",
]

# Legacy default-template files/directories at the mobile project root that
# are superseded by the new src/-based architecture. Only removed if --clean
# is passed. Paths are relative to frontend/mobile.
LEGACY_MOBILE_PATHS = [
    os.path.join("app", "(tabs)"),
    os.path.join("app", "modal.tsx"),
    "components",   # top-level demo components (collapsible, themed-text, etc.)
    "constants",    # top-level demo constants/theme.ts
    "hooks",        # top-level demo hooks (use-color-scheme.ts, etc.)
]


# ==============================================================================
# MOBILE SOURCE FILES (WRITE -- fully owned by this generator)
# ==============================================================================

FILES: dict = {}


# --------------------------------------------------------------------------
# Root-of-mobile config file CONTENT used only when the file doesn't exist
# yet (fresh generation). When it already exists, the merge_* functions
# below are used instead so nothing is destroyed.
# --------------------------------------------------------------------------

FILES["package.json"] = r"""{
  "name": "mobile",
  "version": "1.0.0",
  "private": true,
  "main": "expo-router/entry",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {},
  "devDependencies": {}
}
"""

FILES["app.json"] = r"""{
  "expo": {
    "name": "TRU Connect",
    "slug": "tru-connect",
    "scheme": "truconnect",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "userInterfaceStyle": "automatic",
    "newArchEnabled": true,
    "ios": { "supportsTablet": true, "bundleIdentifier": "com.truepoint.truconnect" },
    "android": {
      "package": "com.truepoint.truconnect",
      "adaptiveIcon": {
        "backgroundImage": "./assets/images/android-icon-background.png",
        "foregroundImage": "./assets/images/android-icon-foreground.png",
        "monochromeImage": "./assets/images/android-icon-monochrome.png"
      }
    },
    "web": { "output": "static", "favicon": "./assets/images/favicon.png" },
    "plugins": [
      "expo-router",
      [
        "expo-splash-screen",
        {
          "image": "./assets/images/splash-icon.png",
          "imageWidth": 200,
          "resizeMode": "contain",
          "backgroundColor": "#0B2447"
        }
      ]
    ],
    "extra": { "apiBaseUrl": "https://api.truconnect.dev/api/v1" },
    "experiments": { "typedRoutes": true }
  }
}
"""

FILES["tsconfig.json"] = r"""{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src", "app", "expo-env.d.ts"]
}
"""

FILES[".gitignore"] = "\n".join(REQUIRED_GITIGNORE_LINES) + "\n"

FILES["babel.config.js"] = r"""module.exports = function (api) {
  api.cache(true);
  return {
    presets: ["babel-preset-expo"],
    // Reanimated 4 moved its worklets engine into the separate
    // react-native-worklets package (also listed in package.json). The
    // Babel plugin path changed accordingly -- do NOT revert this to
    // "react-native-reanimated/plugin", that path is for Reanimated 3.x.
    plugins: ["react-native-worklets/plugin"],
  };
};
"""

FILES[".env.example"] = r"""# TRU Connect Mobile - Environment Variables
EXPO_PUBLIC_API_BASE_URL=https://api.truconnect.dev/api/v1
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=replace-with-google-oauth-web-client-id
"""


# --------------------------------------------------------------------------
# src/theme
# --------------------------------------------------------------------------

FILES["src/theme/colors.ts"] = r"""/**
 * TRU Connect design tokens - colour palette.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 5 (Color Palette)
 *
 * Functional colour roles rather than raw hex usage across the app, so
 * theming (including dark mode) can be layered on without redesign.
 * NEVER hardcode colours in screens/components -- always import from here.
 */
export const palette = {
  truePointBlue: "#0B2447",
  truePointBlueLight: "#19376D",
  truePointBlueDark: "#051230",

  emeraldGreen: "#0FA968",
  emeraldGreenLight: "#3FCB8C",
  emeraldGreenDark: "#0A7A4C",

  neutral900: "#111417",
  neutral700: "#3A3F44",
  neutral500: "#6B7280",
  neutral300: "#D0D4D9",
  neutral100: "#F4F6F8",
  white: "#FFFFFF",

  danger: "#D64545",
  warning: "#E1A400",
  success: "#0FA968",
} as const;

export const lightColors = {
  primary: palette.truePointBlue,
  primaryDark: palette.truePointBlueDark,
  secondary: palette.emeraldGreen,
  success: palette.success,
  warning: palette.warning,
  danger: palette.danger,
  background: palette.white,
  surface: palette.neutral100,
  border: palette.neutral300,
  textPrimary: palette.neutral900,
  textSecondary: palette.neutral500,
  onPrimary: palette.white,
};

export const darkColors = {
  primary: palette.truePointBlueLight,
  primaryDark: palette.truePointBlue,
  secondary: palette.emeraldGreenLight,
  success: palette.emeraldGreenLight,
  warning: palette.warning,
  danger: palette.danger,
  background: palette.neutral900,
  surface: "#1B1F24",
  border: "#2C3238",
  textPrimary: palette.white,
  textSecondary: palette.neutral300,
  onPrimary: palette.white,
};

export type AppColors = typeof lightColors;
"""

FILES["src/theme/spacing.ts"] = r"""/**
 * 8-point spacing grid.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 11 (Layout & Spacing)
 */
export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
} as const;

export const radius = {
  sm: 8,
  md: 12,
  lg: 20,
  pill: 999,
} as const;
"""

FILES["src/theme/typography.ts"] = r"""/**
 * Type scale.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 4 (Typography)
 */
export const typography = {
  display: { fontSize: 28, fontWeight: "700" as const, lineHeight: 36 },
  h1: { fontSize: 22, fontWeight: "600" as const, lineHeight: 30 },
  h2: { fontSize: 18, fontWeight: "600" as const, lineHeight: 26 },
  body: { fontSize: 15, fontWeight: "400" as const, lineHeight: 21 },
  bodySmall: { fontSize: 13, fontWeight: "400" as const, lineHeight: 18 },
  caption: { fontSize: 11, fontWeight: "500" as const, lineHeight: 15 },
};
"""

FILES["src/theme/paperTheme.ts"] = r"""import { MD3LightTheme, MD3DarkTheme } from "react-native-paper";
import { lightColors, darkColors } from "./colors";
import { radius } from "./spacing";

/**
 * React Native Paper theme configuration, extended with TRU Connect's
 * design tokens. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt
 */
export const truConnectLightTheme = {
  ...MD3LightTheme,
  roundness: radius.md,
  colors: {
    ...MD3LightTheme.colors,
    primary: lightColors.primary,
    secondary: lightColors.secondary,
    background: lightColors.background,
    surface: lightColors.surface,
    error: lightColors.danger,
    outline: lightColors.border,
    onPrimary: lightColors.onPrimary,
  },
};

export const truConnectDarkTheme = {
  ...MD3DarkTheme,
  roundness: radius.md,
  colors: {
    ...MD3DarkTheme.colors,
    primary: darkColors.primary,
    secondary: darkColors.secondary,
    background: darkColors.background,
    surface: darkColors.surface,
    error: darkColors.danger,
    outline: darkColors.border,
    onPrimary: darkColors.onPrimary,
  },
};
"""

FILES["src/theme/ThemeProvider.tsx"] = r"""import React from "react";
import { PaperProvider } from "react-native-paper";
import { useColorScheme } from "@/hooks/useColorScheme";
import { truConnectLightTheme, truConnectDarkTheme } from "./paperTheme";

/**
 * Wraps the application with a React Native Paper theme that responds to
 * the device colour scheme.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 1.5 (Accessibility)
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const scheme = useColorScheme();
  const theme = scheme === "dark" ? truConnectDarkTheme : truConnectLightTheme;
  return <PaperProvider theme={theme}>{children}</PaperProvider>;
}
"""


# --------------------------------------------------------------------------
# src/constants
# --------------------------------------------------------------------------

FILES["src/constants/config.ts"] = r"""import Constants from "expo-constants";

/**
 * Central app configuration, sourced from app.json `extra` and/or
 * environment variables. Ref: docs/05_BACKEND_API_SPECIFICATION.txt
 */
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  (Constants.expoConfig?.extra?.apiBaseUrl as string) ||
  "https://api.truconnect.dev/api/v1";

export const OTP_LENGTH = 6;
export const OTP_RESEND_SECONDS = 60;

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "tru_connect_access_token",
  REFRESH_TOKEN: "tru_connect_refresh_token",
  SELECTED_ROLE: "tru_connect_selected_role",
  ONBOARDING_COMPLETE: "tru_connect_onboarding_complete",
} as const;
"""

FILES["src/constants/regex.ts"] = r"""/**
 * Shared validation patterns.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-2
 * (Business/Supplier Registration)
 */

// South African ID number: 13 digits (YYMMDD SSSS C A Z)
export const SA_ID_NUMBER_REGEX = /^\d{13}$/;

// South African mobile number, e.g. 0821234567 or +27821234567
export const SA_MOBILE_NUMBER_REGEX = /^(?:\+27|0)[6-8][0-9]{8}$/;

export const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Minimum 8 characters, at least one letter and one number.
export const PASSWORD_REGEX = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;
"""


# --------------------------------------------------------------------------
# src/services -- infrastructure layer (api client, storage, auth service)
# --------------------------------------------------------------------------

FILES["src/services/storage/secureStorage.ts"] = r"""import * as SecureStore from "expo-secure-store";

/**
 * Thin wrapper around expo-secure-store, used for JWT/refresh token
 * persistence. Ref: docs/04_DATABASE_DESIGN.txt, Section 4.1
 * (Authentication Domain: refresh_tokens)
 */
export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    return SecureStore.getItemAsync(key);
  },
  async setItem(key: string, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value);
  },
  async removeItem(key: string): Promise<void> {
    await SecureStore.deleteItemAsync(key);
  },
};
"""

FILES["src/services/api/apiClient.ts"] = r"""import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { API_BASE_URL, STORAGE_KEYS } from "@/constants/config";
import { secureStorage } from "@/services/storage/secureStorage";

/**
 * Shared Axios instance for all API calls.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 1 (General API
 * Conventions) - versioned base path, JWT bearer auth, consistent error
 * shape.
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    // 401 handling / refresh-token exchange (POST /auth/refresh) would be
    // wired up here in a full implementation. Kept minimal for Phase 1.
    return Promise.reject(error);
  }
);

export interface ApiErrorShape {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}
"""

FILES["src/services/api/queryClient.ts"] = r"""import { QueryClient } from "@tanstack/react-query";

/**
 * Shared React Query client. Ref: docs/03_FRONTEND_COMPONENT_SPECIFICATION.txt
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});
"""

FILES["src/services/auth/authService.ts"] = r"""import { apiClient } from "@/services/api/apiClient";
import {
  AuthTokens,
  AuthUser,
  RegisterPayload,
  SignInPayload,
  VerifyOtpPayload,
} from "@/features/auth/types";

/**
 * Authentication Domain service -- raw API bindings only. Feature-level
 * hooks (src/features/auth/hooks) compose these calls with React Query and
 * app-level side effects (navigation, storage).
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1
 * (Authentication Domain endpoints).
 */
export const authService = {
  async signIn(payload: SignInPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/login", payload);
    return data;
  },

  async register(payload: RegisterPayload): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/register", payload);
    return data;
  },

  async googleSignIn(idToken: string): Promise<{ user: AuthUser; tokens: AuthTokens }> {
    const { data } = await apiClient.post("/auth/google", { idToken });
    return data;
  },

  async requestOtp(destination: string): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/phone/request-otp", { destination });
    return data;
  },

  async verifyOtp(payload: VerifyOtpPayload): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/phone/verify-otp", payload);
    return data;
  },

  async forgotPassword(email: string): Promise<{ success: boolean }> {
    const { data } = await apiClient.post("/auth/forgot-password", { email });
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/auth/logout");
  },
};
"""


# --------------------------------------------------------------------------
# src/navigation -- route-guard helpers (distinct from components/navigation,
# which holds navigation-related UI components)
# --------------------------------------------------------------------------

FILES["src/navigation/routeGuards.ts"] = r"""import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";

/**
 * Route-guard helpers used by Expo Router screens/layouts to decide
 * whether a user may access a given route. Kept framework-agnostic (no
 * direct dependency on expo-router) so it can be unit tested in isolation.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Overall User Flow),
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt.
 */
export async function isAuthenticated(): Promise<boolean> {
  const token = await secureStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  return !!token;
}

export async function getSelectedRole(): Promise<UserRole | null> {
  const role = await secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE);
  return role === "business" || role === "supplier" ? role : null;
}
"""


# --------------------------------------------------------------------------
# src/hooks -- shared, cross-feature hooks
# --------------------------------------------------------------------------

FILES["src/hooks/useColorScheme.ts"] = r"""import { useColorScheme as useRNColorScheme } from "react-native";

/**
 * Re-exported so the rest of the app imports colour scheme from a single,
 * app-owned location (easier to swap for a manual theme toggle later).
 */
export function useColorScheme(): "light" | "dark" {
  return useRNColorScheme() ?? "light";
}
"""

FILES["src/hooks/useCountdown.ts"] = r"""import { useEffect, useState, useCallback } from "react";

/**
 * Simple countdown hook used for the OTP resend timer.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (OTP Verification)
 */
export function useCountdown(initialSeconds: number) {
  const [secondsLeft, setSecondsLeft] = useState(initialSeconds);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const id = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(id);
  }, [secondsLeft]);

  const reset = useCallback(() => setSecondsLeft(initialSeconds), [initialSeconds]);

  return { secondsLeft, isFinished: secondsLeft <= 0, reset };
}
"""

FILES["src/hooks/useNetworkStatus.ts"] = r"""import { useEffect, useState } from "react";
import { Platform } from "react-native";

/**
 * Minimal connectivity hook backing <OfflineBanner />.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (UX Requirements --
 * Offline States).
 *
 * NOTE: this uses `navigator.onLine` on web, which is accurate, and
 * defaults to `true` (assume online) on native platforms, since a native
 * connectivity API (e.g. @react-native-community/netinfo) is not part of
 * the approved dependency list for this phase. When native connectivity
 * detection is required, add that package explicitly and swap the native
 * branch below -- do not substitute a different library ad hoc.
 */
export function useNetworkStatus(): { isOffline: boolean } {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof navigator === "undefined") {
      return;
    }
    const updateStatus = () => setIsOffline(!navigator.onLine);
    updateStatus();
    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);
    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
    };
  }, []);

  return { isOffline };
}
"""


# --------------------------------------------------------------------------
# src/utils
# --------------------------------------------------------------------------

FILES["src/utils/validators.ts"] = r"""import {
  SA_ID_NUMBER_REGEX,
  SA_MOBILE_NUMBER_REGEX,
  EMAIL_REGEX,
  PASSWORD_REGEX,
} from "@/constants/regex";

export const isValidSAIdNumber = (value: string) => SA_ID_NUMBER_REGEX.test(value);
export const isValidSAMobileNumber = (value: string) => SA_MOBILE_NUMBER_REGEX.test(value);
export const isValidEmail = (value: string) => EMAIL_REGEX.test(value);
export const isValidPassword = (value: string) => PASSWORD_REGEX.test(value);
"""


# --------------------------------------------------------------------------
# src/types -- shared cross-feature types
# --------------------------------------------------------------------------

FILES["src/types/index.ts"] = r"""/**
 * Cross-feature shared types. Feature-specific types live under
 * src/features/<feature>/types.ts and should be imported from there
 * directly; only put a type here if more than one feature needs it.
 */
export type { UserRole } from "@/features/auth/types";

export interface ApiListResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}
"""


# --------------------------------------------------------------------------
# src/features/auth
# Ref: docs/04_DATABASE_DESIGN.txt Section 4.1 (Authentication Domain)
#      docs/05_BACKEND_API_SPECIFICATION.txt Section 5.1
#      docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt Sections 1-3
# --------------------------------------------------------------------------

FILES["src/features/auth/types.ts"] = r"""/**
 * Types mirroring the Authentication Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.1) and the Business/Supplier Domains' account-facing fields.
 */
export type UserRole = "business" | "supplier";

export interface AuthUser {
  id: string;
  email: string;
  phoneNumber?: string;
  roles: UserRole[];
  isActive: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export interface SignInPayload {
  email: string;
  password: string;
}

export interface BusinessRegisterPayload {
  role: "business";
  firstName: string;
  lastName: string;
  saIdNumber: string;
  mobileNumber: string;
  email: string;
  password: string;
}

export interface SupplierRegisterPayload {
  role: "supplier";
  businessName: string;
  registrationNumber?: string;
  ownerName: string;
  phoneNumber: string;
  email: string;
  password: string;
}

export type RegisterPayload = BusinessRegisterPayload | SupplierRegisterPayload;

export interface VerifyOtpPayload {
  destination: string; // phone number or email the OTP was sent to
  code: string;
}
"""

FILES["src/features/auth/schemas/authSchemas.ts"] = r"""import { z } from "zod";
import {
  SA_ID_NUMBER_REGEX,
  SA_MOBILE_NUMBER_REGEX,
  PASSWORD_REGEX,
} from "@/constants/regex";

/**
 * Zod validation schemas for authentication forms.
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-2
 * (Business/Supplier Registration).
 */

export const signInSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});
export type SignInFormValues = z.infer<typeof signInSchema>;

export const businessRegisterSchema = z
  .object({
    firstName: z.string().min(1, "First name is required"),
    lastName: z.string().min(1, "Last name is required"),
    saIdNumber: z
      .string()
      .regex(SA_ID_NUMBER_REGEX, "Enter a valid 13-digit South African ID number"),
    mobileNumber: z
      .string()
      .regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid South African mobile number"),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .regex(PASSWORD_REGEX, "Password must be at least 8 characters and include a number"),
    confirmPassword: z.string(),
    acceptPrivacyPolicy: z.literal(true, {
      errorMap: () => ({ message: "You must accept the Privacy Policy to continue" }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type BusinessRegisterFormValues = z.infer<typeof businessRegisterSchema>;

export const supplierRegisterSchema = z
  .object({
    businessName: z.string().min(1, "Business name is required"),
    registrationNumber: z.string().optional(),
    ownerName: z.string().min(1, "Owner name is required"),
    phoneNumber: z
      .string()
      .regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid South African phone number"),
    email: z.string().email("Enter a valid email address"),
    password: z
      .string()
      .regex(PASSWORD_REGEX, "Password must be at least 8 characters and include a number"),
    confirmPassword: z.string(),
    acceptTerms: z.literal(true, {
      errorMap: () => ({ message: "You must accept the Terms to continue" }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type SupplierRegisterFormValues = z.infer<typeof supplierRegisterSchema>;

export const otpSchema = z.object({
  code: z.string().length(6, "Enter the 6-digit code"),
});
export type OtpFormValues = z.infer<typeof otpSchema>;
"""

FILES["src/features/auth/hooks/useAuth.ts"] = r"""import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import { RegisterPayload, SignInPayload } from "../types";

/**
 * React Query mutations composing the auth service with app-level side
 * effects (secure token storage, navigation).
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-3.
 */
export function useSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: SignInPayload) => authService.signIn(payload),
    onSuccess: async ({ tokens }) => {
      await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
      await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
      router.replace("/(dashboard)/home");
    },
  });
}

export function useRegister() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: RegisterPayload) => authService.register(payload),
    onSuccess: () => {
      // Registration triggers OTP verification before dashboard access,
      // per the Authentication Flow (docs/01, Screen 6).
      router.push("/(auth)/verify-otp");
    },
  });
}

export function useGoogleSignIn() {
  const router = useRouter();
  return useMutation({
    mutationFn: (idToken: string) => authService.googleSignIn(idToken),
    onSuccess: async ({ tokens }) => {
      await secureStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
      await secureStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
      router.replace("/(dashboard)/home");
    },
  });
}
"""

FILES["src/features/auth/hooks/useOtp.ts"] = r"""import { useMutation } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { authService } from "@/services/auth/authService";
import { VerifyOtpPayload } from "../types";

/** Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Verification) */
export function useRequestOtp() {
  return useMutation({
    mutationFn: (destination: string) => authService.requestOtp(destination),
  });
}

export function useVerifyOtp() {
  const router = useRouter();
  return useMutation({
    mutationFn: (payload: VerifyOtpPayload) => authService.verifyOtp(payload),
    onSuccess: () => {
      // After verification, the user proceeds to complete their Business
      // Profile Setup wizard (docs/01, Screen 7).
      router.replace("/(business)/profile-setup/step-1-business-info");
    },
  });
}
"""


# --------------------------------------------------------------------------
# src/features/onboarding
# --------------------------------------------------------------------------

FILES["src/features/onboarding/data/onboardingSlides.ts"] = r"""/**
 * Onboarding carousel content.
 * Ref: master prompt "ONBOARDING" section (5 slides incl. Get Started).
 */
export interface OnboardingSlide {
  id: string;
  title: string;
  description: string;
  illustrationKey:
    | "welcome"
    | "business-identity"
    | "verified-trading"
    | "trusted-suppliers"
    | "future-opportunities";
}

export const onboardingSlides: OnboardingSlide[] = [
  {
    id: "slide-1",
    title: "Welcome to TRU Connect",
    description: "Build a trusted digital business identity.",
    illustrationKey: "welcome",
  },
  {
    id: "slide-2",
    title: "Build Your Business Identity",
    description: "Turn everyday trading activity into a verified business profile.",
    illustrationKey: "business-identity",
  },
  {
    id: "slide-3",
    title: "Grow with Verified Trading",
    description:
      "Record your daily business activity and strengthen your financial profile over time.",
    illustrationKey: "verified-trading",
  },
  {
    id: "slide-4",
    title: "Connect with Trusted Suppliers",
    description:
      "Purchase stock from verified suppliers and build stronger business relationships.",
    illustrationKey: "trusted-suppliers",
  },
  {
    id: "slide-5",
    title: "Unlock Future Opportunities",
    description:
      "Your verified business profile can help participating lenders better understand your business performance.",
    illustrationKey: "future-opportunities",
  },
];
"""

FILES["src/features/onboarding/components/OnboardingCarousel.tsx"] = r"""import React, { useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import PagerView from "react-native-pager-view";
import { Text, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";
import { onboardingSlides } from "../data/onboardingSlides";

/**
 * Horizontally swipeable onboarding carousel shown on the Welcome screen,
 * built on react-native-pager-view (the approved dependency for this).
 * Ref: master prompt "ONBOARDING" section.
 */
export function OnboardingCarousel() {
  const theme = useTheme();
  const pagerRef = useRef<PagerView>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <View style={styles.container}>
      <PagerView
        ref={pagerRef}
        style={styles.pager}
        initialPage={0}
        onPageSelected={(e) => setActiveIndex(e.nativeEvent.position)}
      >
        {onboardingSlides.map((slide) => (
          <View key={slide.id} style={styles.slide}>
            <View
              style={[styles.illustrationPlaceholder, { backgroundColor: theme.colors.surfaceVariant }]}
            />
            <Text variant="headlineSmall" style={styles.title}>
              {slide.title}
            </Text>
            <Text variant="bodyMedium" style={[styles.description, { color: theme.colors.onSurfaceVariant }]}>
              {slide.description}
            </Text>
          </View>
        ))}
      </PagerView>

      <View style={styles.dotsRow}>
        {onboardingSlides.map((_, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              {
                backgroundColor: i === activeIndex ? theme.colors.primary : theme.colors.outlineVariant,
                width: i === activeIndex ? 20 : 8,
              },
            ]}
          />
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  pager: { flex: 1 },
  slide: { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: spacing.lg },
  illustrationPlaceholder: { width: "100%", height: 220, borderRadius: 20, marginBottom: spacing.lg },
  title: { textAlign: "center", fontWeight: "700", marginBottom: spacing.sm },
  description: { textAlign: "center" },
  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 6,
    paddingVertical: spacing.lg,
  },
  dot: { height: 8, borderRadius: 4 },
});
"""


# --------------------------------------------------------------------------
# src/features/business
# Ref: docs/04_DATABASE_DESIGN.txt Section 4.2 (Business Domain)
# --------------------------------------------------------------------------

FILES["src/features/business/types.ts"] = r"""/**
 * Types mirroring the Business Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.2) as collected through the Business Profile Setup wizard.
 */
export interface BusinessInfoStep {
  businessName: string;
  tradingName?: string;
  businessType: string;
  industry: string;
  yearsOperating: string;
  addressLine: string;
  latitude?: number;
  longitude?: number;
}

export interface OwnerInfoStep {
  ownerName: string;
  saIdNumber: string;
  phoneNumber: string;
  email: string;
}

export interface TradingInfoStep {
  monthlyRevenue: string;
  customersPerMonth: string;
  averageTransaction: string;
  primarySupplier?: string;
}

export interface DocumentsStep {
  idCopyUri?: string;
  businessPhotoUris: string[];
  tradingProofUri?: string;
  bankStatementUri?: string;
}

export interface BusinessProfileWizardState {
  businessInfo: Partial<BusinessInfoStep>;
  ownerInfo: Partial<OwnerInfoStep>;
  tradingInfo: Partial<TradingInfoStep>;
  documents: Partial<DocumentsStep>;
}
"""

FILES["src/features/business/schemas/businessSchemas.ts"] = r"""import { z } from "zod";
import { SA_ID_NUMBER_REGEX, SA_MOBILE_NUMBER_REGEX } from "@/constants/regex";

/**
 * Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 1 (Business
 * Registration) and docs/04_DATABASE_DESIGN.txt Section 4.2 (businesses,
 * business_addresses tables).
 */
export const businessInfoSchema = z.object({
  businessName: z.string().min(1, "Business name is required"),
  tradingName: z.string().optional(),
  businessType: z.string().min(1, "Select a business type"),
  industry: z.string().min(1, "Select an industry"),
  yearsOperating: z.string().min(1, "Years operating is required"),
  addressLine: z.string().min(1, "Business address is required"),
});
export type BusinessInfoFormValues = z.infer<typeof businessInfoSchema>;

export const ownerInfoSchema = z.object({
  ownerName: z.string().min(1, "Owner name is required"),
  saIdNumber: z.string().regex(SA_ID_NUMBER_REGEX, "Enter a valid South African ID number"),
  phoneNumber: z.string().regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid phone number"),
  email: z.string().email("Enter a valid email address"),
});
export type OwnerInfoFormValues = z.infer<typeof ownerInfoSchema>;

export const tradingInfoSchema = z.object({
  monthlyRevenue: z.string().min(1, "Monthly revenue is required"),
  customersPerMonth: z.string().min(1, "Customers per month is required"),
  averageTransaction: z.string().min(1, "Average transaction value is required"),
  primarySupplier: z.string().optional(),
});
export type TradingInfoFormValues = z.infer<typeof tradingInfoSchema>;
"""

FILES["src/features/business/api/businessApi.ts"] = r"""import { apiClient } from "@/services/api/apiClient";
import { BusinessProfileWizardState } from "../types";

/**
 * Feature-level API bindings for the Business Domain, built on top of the
 * shared apiClient (src/services/api/apiClient.ts).
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2 (Business Domain
 * endpoints) and Section 5.6 (Verification Domain - document submission).
 */
export const businessApi = {
  async submitProfileSetup(state: BusinessProfileWizardState) {
    const { data } = await apiClient.put("/businesses/me", {
      ...state.businessInfo,
      ...state.ownerInfo,
      ...state.tradingInfo,
    });
    return data;
  },

  async uploadDocument(documentType: string, fileUri: string) {
    const formData = new FormData();
    formData.append("document_type", documentType);
    // @ts-expect-error - React Native FormData file shape
    formData.append("file", { uri: fileUri, name: `${documentType}.jpg`, type: "image/jpeg" });
    const { data } = await apiClient.post("/businesses/me/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async getDashboard() {
    const { data } = await apiClient.get("/businesses/me/dashboard");
    return data;
  },

  async getDigitalBusinessProfile() {
    const { data } = await apiClient.get("/businesses/me/profile");
    return data;
  },
};
"""

FILES["src/features/business/hooks/useBusinessProfileWizard.ts"] = r"""import { create } from "zustand";
import { BusinessProfileWizardState } from "../types";

/**
 * In-memory store carrying the Business Profile Setup wizard's state
 * across its 5 steps (docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt,
 * Screen 7), until final submission via businessApi.submitProfileSetup.
 * zustand is an approved dependency for this project.
 */
interface WizardStore extends BusinessProfileWizardState {
  setBusinessInfo: (v: Partial<BusinessProfileWizardState["businessInfo"]>) => void;
  setOwnerInfo: (v: Partial<BusinessProfileWizardState["ownerInfo"]>) => void;
  setTradingInfo: (v: Partial<BusinessProfileWizardState["tradingInfo"]>) => void;
  setDocuments: (v: Partial<BusinessProfileWizardState["documents"]>) => void;
  reset: () => void;
}

const initialState: BusinessProfileWizardState = {
  businessInfo: {},
  ownerInfo: {},
  tradingInfo: {},
  documents: { businessPhotoUris: [] },
};

export const useBusinessProfileWizard = create<WizardStore>((set) => ({
  ...initialState,
  setBusinessInfo: (v) => set((s) => ({ businessInfo: { ...s.businessInfo, ...v } })),
  setOwnerInfo: (v) => set((s) => ({ ownerInfo: { ...s.ownerInfo, ...v } })),
  setTradingInfo: (v) => set((s) => ({ tradingInfo: { ...s.tradingInfo, ...v } })),
  setDocuments: (v) => set((s) => ({ documents: { ...s.documents, ...v } })),
  reset: () => set(initialState),
}));
"""


# --------------------------------------------------------------------------
# src/features/supplier
# Ref: docs/04_DATABASE_DESIGN.txt Section 4.3 (Supplier Domain)
# --------------------------------------------------------------------------

FILES["src/features/supplier/types.ts"] = r"""/**
 * Types mirroring the Supplier Domain (docs/04_DATABASE_DESIGN.txt,
 * Section 4.3) account-registration fields collected in Phase 1.
 */
export interface SupplierRegistrationInfo {
  businessName: string;
  registrationNumber?: string;
  ownerName: string;
  phoneNumber: string;
  email: string;
}
"""

FILES["src/features/supplier/schemas/supplierSchemas.ts"] = r"""import { z } from "zod";
import { SA_MOBILE_NUMBER_REGEX } from "@/constants/regex";

/** Ref: docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Supplier Registration) */
export const supplierInfoSchema = z.object({
  businessName: z.string().min(1, "Business name is required"),
  registrationNumber: z.string().optional(),
  ownerName: z.string().min(1, "Owner name is required"),
  phoneNumber: z.string().regex(SA_MOBILE_NUMBER_REGEX, "Enter a valid phone number"),
  email: z.string().email("Enter a valid email address"),
});
export type SupplierInfoFormValues = z.infer<typeof supplierInfoSchema>;
"""

FILES["src/features/supplier/api/supplierApi.ts"] = r"""import { apiClient } from "@/services/api/apiClient";

/** Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.3 (Supplier Domain) */
export const supplierApi = {
  async getDashboard() {
    const { data } = await apiClient.get("/suppliers/me/dashboard");
    return data;
  },
};
"""


# --------------------------------------------------------------------------
# src/features/dashboard
# --------------------------------------------------------------------------

FILES["src/features/dashboard/types.ts"] = r"""/**
 * Shape of the aggregated dashboard payload.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2
 * (GET /businesses/me/dashboard) and docs/07_DATA_AND_TRUST_ENGINE.txt
 * (Digital Business Profile / Business Health Score).
 */
export interface BusinessDashboardData {
  businessName: string;
  trustScore: number | null;
  todaySales: string;
  tradingActivityCount: number;
}
"""

FILES["src/features/dashboard/hooks/useBusinessDashboard.ts"] = r"""import { useQuery } from "@tanstack/react-query";
import { businessApi } from "@/features/business/api/businessApi";
import type { BusinessDashboardData } from "../types";

/**
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Dashboard)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (Business Health Score).
 */
export function useBusinessDashboard() {
  return useQuery<BusinessDashboardData>({
    queryKey: ["business-dashboard"],
    queryFn: businessApi.getDashboard,
  });
}
"""


# --------------------------------------------------------------------------
# src/components/ui -- basic UI primitives
# --------------------------------------------------------------------------

FILES["src/components/ui/SafeAreaScreen.tsx"] = r"""import React from "react";
import { ViewStyle } from "react-native";
import { SafeAreaView, Edge } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";

interface SafeAreaScreenProps {
  children: React.ReactNode;
  style?: ViewStyle;
  edges?: Edge[];
}

/**
 * Bare safe-area + themed background primitive. ScreenContainer builds on
 * top of this with standard horizontal padding conventions -- composition
 * over duplication, per the master prompt's Development Principles.
 */
export function SafeAreaScreen({ children, style, edges }: SafeAreaScreenProps) {
  const theme = useTheme();
  return (
    <SafeAreaView
      edges={edges}
      style={[{ flex: 1, backgroundColor: theme.colors.background }, style]}
    >
      {children}
    </SafeAreaView>
  );
}
"""

FILES["src/components/ui/ScreenContainer.tsx"] = r"""import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { SafeAreaScreen } from "./SafeAreaScreen";
import { spacing } from "@/theme/spacing";

interface ScreenContainerProps {
  children: React.ReactNode;
  style?: ViewStyle;
  paddingHorizontal?: number;
}

/**
 * Consistent screen shell: safe-area aware, themed background, standard
 * horizontal padding. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt,
 * Section 11 (screen horizontal padding: md baseline).
 */
export function ScreenContainer({
  children,
  style,
  paddingHorizontal = spacing.md,
}: ScreenContainerProps) {
  return (
    <SafeAreaScreen>
      <View style={[styles.flex, { paddingHorizontal }, style]}>{children}</View>
    </SafeAreaScreen>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
});
"""

FILES["src/components/ui/PrimaryButton.tsx"] = r"""import React from "react";
import { Button, ButtonProps } from "react-native-paper";
import { StyleSheet } from "react-native";

/**
 * Primary Button - solid fill, used for the single most important action
 * on a screen. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 8.
 */
export function PrimaryButton({ children, style, ...rest }: ButtonProps) {
  return (
    <Button mode="contained" style={[styles.button, style]} contentStyle={styles.content} {...rest}>
      {children}
    </Button>
  );
}

const styles = StyleSheet.create({
  button: { borderRadius: 12 },
  content: { height: 52 },
});
"""

FILES["src/components/ui/SecondaryButton.tsx"] = r"""import React from "react";
import { Button, ButtonProps } from "react-native-paper";
import { StyleSheet } from "react-native";

/**
 * Secondary Button - outlined, used for supporting actions.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 8.
 */
export function SecondaryButton({ children, style, ...rest }: ButtonProps) {
  return (
    <Button mode="outlined" style={[styles.button, style]} contentStyle={styles.content} {...rest}>
      {children}
    </Button>
  );
}

const styles = StyleSheet.create({
  button: { borderRadius: 12 },
  content: { height: 52 },
});
"""

FILES["src/components/ui/ProgressStepper.tsx"] = r"""import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";

interface ProgressStepperProps {
  totalSteps: number;
  currentStep: number; // 1-indexed
  stepLabels?: string[];
}

/**
 * Visible step indicator for multi-step forms.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 9 (Forms) and
 * docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Profile Setup
 * Wizard, 5 steps).
 */
export function ProgressStepper({ totalSteps, currentStep, stepLabels }: ProgressStepperProps) {
  const theme = useTheme();
  return (
    <View>
      <View style={styles.row}>
        {Array.from({ length: totalSteps }).map((_, i) => {
          const stepIndex = i + 1;
          const isComplete = stepIndex < currentStep;
          const isActive = stepIndex === currentStep;
          return (
            <View
              key={i}
              style={[
                styles.segment,
                {
                  backgroundColor:
                    isComplete || isActive ? theme.colors.primary : theme.colors.outline,
                },
              ]}
            />
          );
        })}
      </View>
      {stepLabels && (
        <Text variant="bodySmall" style={{ marginTop: spacing.sm, color: theme.colors.onSurfaceVariant }}>
          Step {currentStep} of {totalSteps}: {stepLabels[currentStep - 1]}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: 6 },
  segment: { flex: 1, height: 6, borderRadius: 3 },
});
"""


# --------------------------------------------------------------------------
# src/components/cards
# --------------------------------------------------------------------------

FILES["src/components/cards/AppCard.tsx"] = r"""import React from "react";
import { StyleSheet, View, ViewStyle } from "react-native";
import { useTheme } from "react-native-paper";
import { radius, spacing } from "@/theme/spacing";

interface AppCardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  selected?: boolean;
}

/**
 * Shared card shell: rounded corners, soft shadow, consistent padding.
 * Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 7 (Cards).
 */
export function AppCard({ children, style, selected }: AppCardProps) {
  const theme = useTheme();
  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: selected ? theme.colors.primary : "transparent",
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 2,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
});
"""

FILES["src/components/cards/RoleCard.tsx"] = r"""import React, { useEffect } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import Animated, { useSharedValue, useAnimatedStyle, withTiming } from "react-native-reanimated";
import { AppCard } from "./AppCard";
import { spacing } from "@/theme/spacing";

interface RoleCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  selected: boolean;
  onPress: () => void;
}

/**
 * Role Selection card (Business Owner / Supplier), with a subtle Reanimated
 * scale animation on selection. Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (Role Selection screen) and master prompt "ANIMATIONS" (subtle, fast,
 * professional).
 */
export function RoleCard({ title, description, icon, selected, onPress }: RoleCardProps) {
  const theme = useTheme();
  const scale = useSharedValue(1);

  useEffect(() => {
    scale.value = withTiming(selected ? 1.02 : 1, { duration: 150 });
  }, [selected, scale]);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityState={{ selected }}>
      <Animated.View style={animatedStyle}>
        <AppCard selected={selected} style={styles.card}>
          <View style={styles.iconWrap}>{icon}</View>
          <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.sm }}>
            {title}
          </Text>
          <Text
            variant="bodyMedium"
            style={{ color: theme.colors.onSurfaceVariant, marginTop: spacing.xs }}
          >
            {description}
          </Text>
        </AppCard>
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { marginBottom: spacing.md },
  iconWrap: { width: 48, height: 48, justifyContent: "center", alignItems: "flex-start" },
});
"""

FILES["src/components/cards/FeatureTile.tsx"] = r"""import React from "react";
import { Pressable, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { AppCard } from "./AppCard";
import { spacing } from "@/theme/spacing";

interface FeatureTileProps {
  label: string;
  icon: React.ReactNode;
  onPress?: () => void;
}

/**
 * Compact tappable tile used for dashboard Quick Actions (Upload Receipts,
 * Add Supplier, Verify Information). Ref: master prompt "REUSABLE
 * COMPONENTS" (FeatureTile) and docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (Home Dashboard -- Quick Actions).
 */
export function FeatureTile({ label, icon, onPress }: FeatureTileProps) {
  const theme = useTheme();
  return (
    <Pressable onPress={onPress} style={styles.pressable}>
      <AppCard style={styles.tile}>
        {icon}
        <Text
          variant="bodySmall"
          style={{ color: theme.colors.onSurface, marginTop: spacing.xs, textAlign: "center" }}
        >
          {label}
        </Text>
      </AppCard>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressable: { flex: 1 },
  tile: { alignItems: "center", justifyContent: "center", paddingVertical: spacing.md },
});
"""


# --------------------------------------------------------------------------
# src/components/forms
# --------------------------------------------------------------------------

FILES["src/components/forms/FormTextField.tsx"] = r"""import React from "react";
import { Controller, Control, FieldValues, Path } from "react-hook-form";
import { HelperText, TextInput, TextInputProps } from "react-native-paper";
import { View } from "react-native";
import { spacing } from "@/theme/spacing";

interface FormTextFieldProps<T extends FieldValues> extends Omit<TextInputProps, "value" | "onChangeText"> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

/**
 * React Hook Form <-> React Native Paper TextInput bridge, with inline
 * validation error display. Ref: docs/02_SYSTEM_UI_UX_SPECIFICATION.txt,
 * Section 9 (Forms) - labels always visible, inline errors in Danger role.
 */
export function FormTextField<T extends FieldValues>({
  control,
  name,
  label,
  secureTextEntry,
  ...rest
}: FormTextFieldProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, onBlur, value }, fieldState: { error } }) => (
        <View style={{ marginBottom: spacing.md }}>
          <TextInput
            mode="outlined"
            label={label}
            value={value ?? ""}
            onChangeText={onChange}
            onBlur={onBlur}
            secureTextEntry={secureTextEntry}
            error={!!error}
            {...rest}
          />
          <HelperText type="error" visible={!!error}>
            {error?.message ?? " "}
          </HelperText>
        </View>
      )}
    />
  );
}
"""

FILES["src/components/forms/PasswordField.tsx"] = r"""import React, { useState } from "react";
import { Control, FieldValues, Path } from "react-hook-form";
import { TextInputProps } from "react-native-paper";
import { Eye, EyeOff } from "lucide-react-native";
import { TextInput as RNPTextInput } from "react-native-paper";
import { useTheme } from "react-native-paper";
import { FormTextField } from "./FormTextField";

interface PasswordFieldProps<T extends FieldValues> extends Omit<TextInputProps, "value" | "onChangeText" | "secureTextEntry"> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

/**
 * Password input with a show/hide toggle (lucide-react-native icons).
 * Ref: master prompt "REUSABLE COMPONENTS" (PasswordField).
 */
export function PasswordField<T extends FieldValues>({ control, name, label, ...rest }: PasswordFieldProps<T>) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  return (
    <FormTextField
      control={control}
      name={name}
      label={label}
      secureTextEntry={!visible}
      right={
        <RNPTextInput.Icon
          icon={() =>
            visible ? (
              <EyeOff size={20} color={theme.colors.onSurfaceVariant} />
            ) : (
              <Eye size={20} color={theme.colors.onSurfaceVariant} />
            )
          }
          onPress={() => setVisible((v) => !v)}
          forceTextInputFocus={false}
        />
      }
      {...rest}
    />
  );
}
"""

FILES["src/components/forms/OtpInput.tsx"] = r"""import React, { useRef } from "react";
import { View, TextInput as RNTextInput, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { OTP_LENGTH } from "@/constants/config";
import { spacing, radius } from "@/theme/spacing";

interface OtpInputProps {
  value: string;
  onChange: (value: string) => void;
  length?: number;
}

/**
 * Segmented OTP entry boxes. Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
 * (OTP Verification screen).
 */
export function OtpInput({ value, onChange, length = OTP_LENGTH }: OtpInputProps) {
  const theme = useTheme();
  const inputRef = useRef<RNTextInput>(null);
  const digits = value.split("");

  return (
    <View style={styles.row}>
      {/* Single hidden input drives all boxes for reliable focus/keyboard handling */}
      <RNTextInput
        ref={inputRef}
        value={value}
        onChangeText={(text) => onChange(text.replace(/[^0-9]/g, "").slice(0, length))}
        keyboardType="number-pad"
        maxLength={length}
        style={styles.hiddenInput}
        autoFocus
      />
      {Array.from({ length }).map((_, i) => {
        const filled = !!digits[i];
        return (
          <View
            key={i}
            style={[
              styles.box,
              {
                borderColor: filled ? theme.colors.primary : theme.colors.outline,
                backgroundColor: theme.colors.surface,
              },
            ]}
          >
            <View>
              <RNTextInput
                editable={false}
                value={digits[i] ?? ""}
                style={[styles.boxText, { color: theme.colors.onSurface }]}
              />
            </View>
          </View>
        );
      })}
    </View>
  );
}

const BOX_SIZE = 48;

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", marginVertical: spacing.lg },
  box: {
    width: BOX_SIZE,
    height: BOX_SIZE,
    borderRadius: radius.sm,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  boxText: { fontSize: 20, fontWeight: "700", textAlign: "center" },
  hiddenInput: { position: "absolute", opacity: 0, height: 1, width: 1 },
});
"""


# --------------------------------------------------------------------------
# src/components/feedback
# --------------------------------------------------------------------------

FILES["src/components/feedback/LoadingOverlay.tsx"] = r"""import React from "react";
import { View, StyleSheet, Modal } from "react-native";
import { ActivityIndicator, Text, useTheme } from "react-native-paper";
import { spacing } from "@/theme/spacing";

interface LoadingOverlayProps {
  visible: boolean;
  label?: string;
}

/**
 * Full-screen semi-transparent overlay with a spinner, used for blocking
 * async actions (e.g. submitting the Business Profile wizard) without
 * navigating away from the current screen.
 * Ref: master prompt "REUSABLE COMPONENTS" (LoadingOverlay) and
 * docs/02_SYSTEM_UI_UX_SPECIFICATION.txt, Section 2.3 (Loading States).
 */
export function LoadingOverlay({ visible, label = "Loading..." }: LoadingOverlayProps) {
  const theme = useTheme();
  if (!visible) return null;

  return (
    <Modal transparent visible={visible} animationType="fade">
      <View style={[styles.backdrop, { backgroundColor: "rgba(0,0,0,0.35)" }]}>
        <View style={[styles.card, { backgroundColor: theme.colors.surface }]}>
          <ActivityIndicator animating color={theme.colors.primary} size="large" />
          <Text style={{ marginTop: spacing.sm, color: theme.colors.onSurfaceVariant }}>{label}</Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center" },
  card: { borderRadius: 16, padding: spacing.xl, alignItems: "center", minWidth: 160 },
});
"""

FILES["src/components/feedback/EmptyState.tsx"] = r"""import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";

interface EmptyStateProps {
  icon?: React.ReactNode;
  message: string;
  actionLabel?: string;
  onActionPress?: () => void;
}

/** Ref: master prompt "REUSABLE COMPONENTS" (EmptyState) */
export function EmptyState({ icon, message, actionLabel, onActionPress }: EmptyStateProps) {
  const theme = useTheme();
  return (
    <View style={styles.container}>
      {icon}
      <Text style={{ color: theme.colors.onSurfaceVariant, textAlign: "center", marginTop: spacing.sm }}>
        {message}
      </Text>
      {actionLabel && onActionPress && (
        <PrimaryButton onPress={onActionPress} style={{ marginTop: spacing.md }}>
          {actionLabel}
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
});
"""

FILES["src/components/feedback/ErrorState.tsx"] = r"""import React from "react";
import { View, StyleSheet } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

/** Ref: master prompt "REUSABLE COMPONENTS" (ErrorState) */
export function ErrorState({ message = "Something went wrong. Please try again.", onRetry }: ErrorStateProps) {
  const theme = useTheme();
  return (
    <View style={styles.container}>
      <Text style={{ color: theme.colors.error, textAlign: "center" }}>{message}</Text>
      {onRetry && (
        <PrimaryButton onPress={onRetry} style={{ marginTop: spacing.md }}>
          Try Again
        </PrimaryButton>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
});
"""

FILES["src/components/feedback/OfflineBanner.tsx"] = r"""import React from "react";
import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";
import { WifiOff } from "lucide-react-native";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";

/**
 * Slim banner shown at the top of the app when offline. Mounted once in
 * app/_layout.tsx so it is visible across every screen.
 * Ref: master prompt "REUSABLE COMPONENTS" (OfflineBanner) and "USER
 * EXPERIENCE" (Offline States).
 */
export function OfflineBanner() {
  const { isOffline } = useNetworkStatus();
  if (!isOffline) return null;

  return (
    <View style={styles.banner}>
      <WifiOff size={16} color={palette.white} />
      <Text style={styles.text}>You're offline. Some information may be out of date.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: spacing.xs,
    backgroundColor: palette.danger,
  },
  text: { color: palette.white, fontSize: 12, fontWeight: "600" },
});
"""


# --------------------------------------------------------------------------
# src/components/navigation
# --------------------------------------------------------------------------

FILES["src/components/navigation/ScreenHeader.tsx"] = r"""import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { ChevronLeft } from "lucide-react-native";
import { Pressable } from "react-native";
import { spacing } from "@/theme/spacing";

interface ScreenHeaderProps {
  title?: string;
  onBack?: () => void;
}

/**
 * Reusable in-screen header with an optional back button, used on wizard
 * steps and other stacked screens that need a consistent title/back
 * affordance without a full native navigation header.
 * Ref: master prompt component architecture (components/navigation/).
 */
export function ScreenHeader({ title, onBack }: ScreenHeaderProps) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      {onBack && (
        <Pressable onPress={onBack} hitSlop={12} style={styles.backButton}>
          <ChevronLeft size={24} color={theme.colors.onSurface} />
        </Pressable>
      )}
      {title && (
        <Text variant="titleMedium" style={{ fontWeight: "700" }}>
          {title}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginBottom: spacing.md },
  backButton: { padding: spacing.xs },
});
"""


# --------------------------------------------------------------------------
# app/ -- Expo Router routes (ROUTING ONLY, per master prompt architecture;
# all business logic lives in src/ and is imported from here).
# --------------------------------------------------------------------------

FILES["app/_layout.tsx"] = r"""import React from "react";
import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { StatusBar } from "expo-status-bar";
import { ThemeProvider } from "@/theme/ThemeProvider";
import { queryClient } from "@/services/api/queryClient";
import { OfflineBanner } from "@/components/feedback/OfflineBanner";

/**
 * Root layout: wires up theming, React Query, and gesture handling for
 * the whole app, and mounts the global OfflineBanner.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Overall User Flow)
 * and docs/02_SYSTEM_UI_UX_SPECIFICATION.txt.
 *
 * NOTE: this replaces the default Expo template's root layout (which
 * rendered the demo (tabs) navigator). Run this generator with --clean to
 * also remove the now-unused app/(tabs) and app/modal.tsx demo screens.
 */
export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <StatusBar style="auto" />
          <OfflineBanner />
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="(onboarding)" />
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(business)" />
            <Stack.Screen name="(dashboard)" />
          </Stack>
        </ThemeProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
"""

FILES["app/index.tsx"] = r"""import React, { useEffect } from "react";
import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import Animated, { useSharedValue, useAnimatedStyle, withTiming, Easing } from "react-native-reanimated";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";

/**
 * Splash Screen.
 * Displays logo + tagline on a gradient background with a subtle
 * Reanimated fade-in, then automatically navigates to Welcome after 2s.
 * Ref: master prompt Authentication Flow (Splash -> Welcome).
 *
 * NOTE: this is the top-level "/" route. It supersedes the default
 * template's app/(tabs)/index.tsx, which also maps to "/". Run this
 * generator with --clean to remove the (tabs) group and avoid the route
 * name collision.
 */
export default function SplashScreen() {
  const router = useRouter();
  const opacity = useSharedValue(0);

  useEffect(() => {
    opacity.value = withTiming(1, { duration: 500, easing: Easing.out(Easing.quad) });
    const timer = setTimeout(() => {
      router.replace("/(onboarding)/welcome");
    }, 2000);
    return () => clearTimeout(timer);
  }, [router, opacity]);

  const animatedStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));

  return (
    <LinearGradient
      colors={[palette.truePointBlueDark, palette.truePointBlue]}
      style={styles.container}
    >
      <Animated.View style={[styles.center, animatedStyle]}>
        <View style={styles.logoPlaceholder} />
        <Text variant="headlineMedium" style={styles.wordmark}>
          TRU Connect
        </Text>
        <Text variant="bodyMedium" style={styles.tagline}>
          Build Trust. Unlock Opportunity.
        </Text>
      </Animated.View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  center: { alignItems: "center" },
  logoPlaceholder: {
    width: 88,
    height: 88,
    borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.15)",
    marginBottom: spacing.lg,
  },
  wordmark: { color: "#FFFFFF", fontWeight: "700" },
  tagline: { color: "rgba(255,255,255,0.85)", marginTop: spacing.sm },
});
"""

FILES["app/(onboarding)/_layout.tsx"] = r"""import { Stack } from "expo-router";

export default function OnboardingLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
"""

FILES["app/(onboarding)/welcome.tsx"] = r"""import React from "react";
import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { OnboardingCarousel } from "@/features/onboarding/components/OnboardingCarousel";
import { spacing } from "@/theme/spacing";

/**
 * Welcome Screen, with the horizontally swipeable onboarding carousel.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 2) and
 * master prompt "ONBOARDING" section.
 */
export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <ScreenContainer>
      <View style={styles.carouselWrap}>
        <OnboardingCarousel />
      </View>

      <Text variant="bodySmall" style={styles.privacyNotice}>
        By continuing, you agree to TRU Connect's Terms and Privacy Policy.
      </Text>

      <View style={styles.actions}>
        <PrimaryButton onPress={() => router.push("/(onboarding)/role-selection")}>
          Get Started
        </PrimaryButton>
        <SecondaryButton
          onPress={() => router.push("/(auth)/sign-in")}
          style={{ marginTop: spacing.sm }}
        >
          I already have an account
        </SecondaryButton>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  carouselWrap: { flex: 1, justifyContent: "center" },
  privacyNotice: { textAlign: "center", marginBottom: spacing.md, opacity: 0.7 },
  actions: { marginBottom: spacing.lg },
});
"""

FILES["app/(onboarding)/role-selection.tsx"] = r"""import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { Store, Warehouse } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { RoleCard } from "@/components/cards/RoleCard";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing } from "@/theme/spacing";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";

/**
 * Role Selection ("Who are you joining as?").
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 3) and
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-2 (role determines
 * the registration form shown next).
 */
export default function RoleSelectionScreen() {
  const router = useRouter();
  const theme = useTheme();
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);

  const handleContinue = async () => {
    if (!selectedRole) return;
    await secureStorage.setItem(STORAGE_KEYS.SELECTED_ROLE, selectedRole);
    router.push("/(auth)/create-account");
  };

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Who are you joining as?
      </Text>

      <View style={styles.cards}>
        <RoleCard
          title="Business Owner"
          description="Build your business identity and trading profile."
          icon={<Store size={28} color={theme.colors.primary} />}
          selected={selectedRole === "business"}
          onPress={() => setSelectedRole("business")}
        />
        <RoleCard
          title="Supplier"
          description="Connect with businesses and grow your sales network."
          icon={<Warehouse size={28} color={theme.colors.primary} />}
          selected={selectedRole === "supplier"}
          onPress={() => setSelectedRole("supplier")}
        />
      </View>

      <PrimaryButton disabled={!selectedRole} onPress={handleContinue} style={styles.continueBtn}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  cards: { flex: 1 },
  continueBtn: { marginBottom: spacing.lg },
});
"""

FILES["app/(auth)/_layout.tsx"] = r"""import { Stack } from "expo-router";

export default function AuthLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
"""

FILES["app/(auth)/sign-in.tsx"] = r"""import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, Checkbox, Divider } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { signInSchema, SignInFormValues } from "@/features/auth/schemas/authSchemas";
import { useSignIn } from "@/features/auth/hooks/useAuth";
import { spacing } from "@/theme/spacing";

/**
 * Sign In screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 4) and
 * docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.1 (POST /auth/login).
 */
export default function SignInScreen() {
  const signIn = useSignIn();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { isSubmitting },
  } = useForm<SignInFormValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  const rememberMe = watch("rememberMe");

  const onSubmit = (values: SignInFormValues) => {
    signIn.mutate({ email: values.email, password: values.password });
  };

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Welcome back
      </Text>

      <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
      <PasswordField control={control} name="password" label="Password" />

      <View style={styles.row}>
        <Checkbox
          status={rememberMe ? "checked" : "unchecked"}
          onPress={() => setValue("rememberMe", !rememberMe)}
        />
        <Text onPress={() => setValue("rememberMe", !rememberMe)}>Remember Me</Text>
        <View style={{ flex: 1 }} />
        <Text style={styles.link}>Forgot Password?</Text>
      </View>

      {signIn.isError && (
        <Text style={styles.errorText}>
          We couldn't sign you in. Please check your details and try again.
        </Text>
      )}

      <PrimaryButton
        onPress={handleSubmit(onSubmit)}
        loading={isSubmitting || signIn.isPending}
        style={{ marginTop: spacing.md }}
      >
        Sign In
      </PrimaryButton>

      <Divider style={{ marginVertical: spacing.lg }} />
      <Text style={styles.orText}>OR</Text>

      <SecondaryButton icon="google" onPress={() => {}} style={{ marginTop: spacing.md }}>
        Continue with Google
      </SecondaryButton>

      <View style={styles.footerRow}>
        <Text>Don't have an account? </Text>
        <Link href="/(onboarding)/role-selection">
          <Text style={styles.link}>Create Account</Text>
        </Link>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.md },
  link: { fontWeight: "600" },
  orText: { textAlign: "center", opacity: 0.6, marginTop: -spacing.lg },
  errorText: { color: "#D64545", marginBottom: spacing.sm },
  footerRow: { flexDirection: "row", justifyContent: "center", marginTop: spacing.lg },
});
"""

FILES["app/(auth)/create-account.tsx"] = r"""import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text, Checkbox } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PasswordField } from "@/components/forms/PasswordField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import {
  businessRegisterSchema,
  BusinessRegisterFormValues,
  supplierRegisterSchema,
  SupplierRegisterFormValues,
} from "@/features/auth/schemas/authSchemas";
import { useRegister } from "@/features/auth/hooks/useAuth";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";
import { spacing } from "@/theme/spacing";

/**
 * Create Account screen. Renders a different form depending on the role
 * chosen on the Role Selection screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 5) and
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-2.
 */
export default function CreateAccountScreen() {
  const register = useRegister();
  const [role, setRole] = useState<UserRole>("business");

  useEffect(() => {
    secureStorage.getItem(STORAGE_KEYS.SELECTED_ROLE).then((stored) => {
      if (stored === "supplier" || stored === "business") setRole(stored);
    });
  }, []);

  return role === "business" ? (
    <BusinessRegisterForm onSubmit={(values) => register.mutate({ role: "business", ...values })} isSubmitting={register.isPending} />
  ) : (
    <SupplierRegisterForm onSubmit={(values) => register.mutate({ role: "supplier", ...values })} isSubmitting={register.isPending} />
  );
}

function BusinessRegisterForm({
  onSubmit,
  isSubmitting,
}: {
  onSubmit: (values: BusinessRegisterFormValues) => void;
  isSubmitting: boolean;
}) {
  const { control, handleSubmit, watch, setValue } = useForm<BusinessRegisterFormValues>({
    resolver: zodResolver(businessRegisterSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      saIdNumber: "",
      mobileNumber: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptPrivacyPolicy: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptPrivacyPolicy");

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Create Your Business Account
      </Text>
      <FormTextField control={control} name="firstName" label="First Name" />
      <FormTextField control={control} name="lastName" label="Last Name" />
      <FormTextField control={control} name="saIdNumber" label="South African ID Number" keyboardType="number-pad" />
      <FormTextField control={control} name="mobileNumber" label="Mobile Number" keyboardType="phone-pad" />
      <FormTextField control={control} name="email" label="Email Address" autoCapitalize="none" keyboardType="email-address" />
      <PasswordField control={control} name="password" label="Password" />
      <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

      <View style={styles.row}>
        <Checkbox
          status={accepted ? "checked" : "unchecked"}
          onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true)}
        />
        <Text onPress={() => setValue("acceptPrivacyPolicy", !accepted as unknown as true)}>
          I accept the Privacy Policy
        </Text>
      </View>

      <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
        Create Account
      </PrimaryButton>
    </ScreenContainer>
  );
}

function SupplierRegisterForm({
  onSubmit,
  isSubmitting,
}: {
  onSubmit: (values: SupplierRegisterFormValues) => void;
  isSubmitting: boolean;
}) {
  const { control, handleSubmit, watch, setValue } = useForm<SupplierRegisterFormValues>({
    resolver: zodResolver(supplierRegisterSchema),
    defaultValues: {
      businessName: "",
      registrationNumber: "",
      ownerName: "",
      phoneNumber: "",
      email: "",
      password: "",
      confirmPassword: "",
      acceptTerms: undefined as unknown as true,
    },
  });
  const accepted = watch("acceptTerms");

  return (
    <ScreenContainer>
      <Text variant="headlineSmall" style={styles.title}>
        Create Your Supplier Account
      </Text>
      <FormTextField control={control} name="businessName" label="Business Name" />
      <FormTextField control={control} name="registrationNumber" label="Registration Number (optional)" />
      <FormTextField control={control} name="ownerName" label="Owner Name" />
      <FormTextField control={control} name="phoneNumber" label="Phone Number" keyboardType="phone-pad" />
      <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />
      <PasswordField control={control} name="password" label="Password" />
      <PasswordField control={control} name="confirmPassword" label="Confirm Password" />

      <View style={styles.row}>
        <Checkbox
          status={accepted ? "checked" : "unchecked"}
          onPress={() => setValue("acceptTerms", !accepted as unknown as true)}
        />
        <Text onPress={() => setValue("acceptTerms", !accepted as unknown as true)}>I accept the Terms</Text>
      </View>

      <PrimaryButton onPress={handleSubmit(onSubmit)} loading={isSubmitting} style={{ marginTop: spacing.md }}>
        Create Account
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginTop: spacing.lg, marginBottom: spacing.lg },
  row: { flexDirection: "row", alignItems: "center", marginBottom: spacing.md },
});
"""

FILES["app/(auth)/verify-otp.tsx"] = r"""import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { Smartphone } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { OtpInput } from "@/components/forms/OtpInput";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { useCountdown } from "@/hooks/useCountdown";
import { useRequestOtp, useVerifyOtp } from "@/features/auth/hooks/useOtp";
import { OTP_LENGTH, OTP_RESEND_SECONDS } from "@/constants/config";
import { spacing } from "@/theme/spacing";

/**
 * OTP Verification screen.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 6) and
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Section 2 (Verification).
 */
export default function VerifyOtpScreen() {
  const theme = useTheme();
  const [code, setCode] = useState("");
  const { secondsLeft, isFinished, reset } = useCountdown(OTP_RESEND_SECONDS);
  const requestOtp = useRequestOtp();
  const verifyOtp = useVerifyOtp();

  const handleResend = () => {
    requestOtp.mutate("current-user-destination");
    reset();
  };

  const handleVerify = () => {
    verifyOtp.mutate({ destination: "current-user-destination", code });
  };

  return (
    <ScreenContainer>
      <View style={styles.iconWrap}>
        <Smartphone size={56} color={theme.colors.primary} />
      </View>

      <Text variant="headlineSmall" style={styles.title}>
        Verify Your Number
      </Text>
      <Text style={styles.description}>
        Enter the {OTP_LENGTH}-digit verification code sent to your phone.
      </Text>

      <OtpInput value={code} onChange={setCode} length={OTP_LENGTH} />

      {verifyOtp.isError && (
        <Text style={styles.errorText}>That code didn't work. Please try again.</Text>
      )}

      <Text
        style={[styles.resend, isFinished ? styles.resendActive : styles.resendInactive]}
        onPress={isFinished ? handleResend : undefined}
      >
        {isFinished ? "Resend Code" : `Resend code in ${secondsLeft}s`}
      </Text>

      <PrimaryButton
        onPress={handleVerify}
        disabled={code.length !== OTP_LENGTH}
        loading={verifyOtp.isPending}
        style={{ marginTop: spacing.lg }}
      >
        Verify
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  iconWrap: { alignItems: "center", marginTop: spacing.xl },
  title: { fontWeight: "700", textAlign: "center", marginTop: spacing.lg },
  description: { textAlign: "center", opacity: 0.7, marginTop: spacing.sm },
  resend: { textAlign: "center", marginTop: spacing.md },
  resendActive: { fontWeight: "700" },
  resendInactive: { opacity: 0.5 },
  errorText: { color: "#D64545", textAlign: "center", marginTop: spacing.sm },
});
"""

FILES["app/(business)/_layout.tsx"] = r"""import { Stack } from "expo-router";

export default function BusinessLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
"""

FILES["app/(business)/profile-setup/_layout.tsx"] = r"""import { Stack } from "expo-router";

/**
 * Business Profile Setup (Multi-step Wizard) layout.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Steps 1-5).
 */
export default function ProfileSetupLayout() {
  return <Stack screenOptions={{ headerShown: false, gestureEnabled: false }} />;
}
"""

FILES["app/(business)/profile-setup/step-1-business-info.tsx"] = r"""import React from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { businessInfoSchema, BusinessInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 1 - Business Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 1)
 * and docs/04_DATABASE_DESIGN.txt Section 4.2 (businesses,
 * business_addresses).
 */
export default function BusinessInfoStep() {
  const router = useRouter();
  const { businessInfo, setBusinessInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<BusinessInfoFormValues>({
    resolver: zodResolver(businessInfoSchema),
    defaultValues: {
      businessName: businessInfo.businessName ?? "",
      tradingName: businessInfo.tradingName ?? "",
      businessType: businessInfo.businessType ?? "",
      industry: businessInfo.industry ?? "",
      yearsOperating: businessInfo.yearsOperating ?? "",
      addressLine: businessInfo.addressLine ?? "",
    },
  });

  const onNext = (values: BusinessInfoFormValues) => {
    setBusinessInfo(values);
    router.push("/(business)/profile-setup/step-2-owner-info");
  };

  return (
    <ScreenContainer>
      <ProgressStepper totalSteps={5} currentStep={1} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Business Information
      </Text>

      <FormTextField control={control} name="businessName" label="Business Name" />
      <FormTextField control={control} name="tradingName" label="Trading Name (optional)" />
      <FormTextField control={control} name="businessType" label="Business Type" />
      <FormTextField control={control} name="industry" label="Industry" />
      <FormTextField control={control} name="yearsOperating" label="Years Operating" keyboardType="number-pad" />
      <FormTextField control={control} name="addressLine" label="Business Address" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
"""

FILES["app/(business)/profile-setup/step-2-owner-info.tsx"] = r"""import React from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { ownerInfoSchema, OwnerInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 2 - Owner Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 2).
 */
export default function OwnerInfoStep() {
  const router = useRouter();
  const { ownerInfo, setOwnerInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<OwnerInfoFormValues>({
    resolver: zodResolver(ownerInfoSchema),
    defaultValues: {
      ownerName: ownerInfo.ownerName ?? "",
      saIdNumber: ownerInfo.saIdNumber ?? "",
      phoneNumber: ownerInfo.phoneNumber ?? "",
      email: ownerInfo.email ?? "",
    },
  });

  const onNext = (values: OwnerInfoFormValues) => {
    setOwnerInfo(values);
    router.push("/(business)/profile-setup/step-3-trading-info");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={2} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Owner Information
      </Text>

      <FormTextField control={control} name="ownerName" label="Owner Name" />
      <FormTextField control={control} name="saIdNumber" label="ID Number" keyboardType="number-pad" />
      <FormTextField control={control} name="phoneNumber" label="Phone" keyboardType="phone-pad" />
      <FormTextField control={control} name="email" label="Email" autoCapitalize="none" keyboardType="email-address" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
"""

FILES["app/(business)/profile-setup/step-3-trading-info.tsx"] = r"""import React from "react";
import { StyleSheet } from "react-native";
import { Text } from "react-native-paper";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FormTextField } from "@/components/forms/FormTextField";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { tradingInfoSchema, TradingInfoFormValues } from "@/features/business/schemas/businessSchemas";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 3 - Trading Information.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 3)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (this data seeds the initial
 * Digital Business Profile / Business Health Score baseline).
 */
export default function TradingInfoStep() {
  const router = useRouter();
  const { tradingInfo, setTradingInfo } = useBusinessProfileWizard();
  const { control, handleSubmit } = useForm<TradingInfoFormValues>({
    resolver: zodResolver(tradingInfoSchema),
    defaultValues: {
      monthlyRevenue: tradingInfo.monthlyRevenue ?? "",
      customersPerMonth: tradingInfo.customersPerMonth ?? "",
      averageTransaction: tradingInfo.averageTransaction ?? "",
      primarySupplier: tradingInfo.primarySupplier ?? "",
    },
  });

  const onNext = (values: TradingInfoFormValues) => {
    setTradingInfo(values);
    router.push("/(business)/profile-setup/step-4-documents");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={3} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Trading Information
      </Text>

      <FormTextField control={control} name="monthlyRevenue" label="Monthly Revenue" keyboardType="numeric" />
      <FormTextField control={control} name="customersPerMonth" label="Customers Per Month" keyboardType="number-pad" />
      <FormTextField control={control} name="averageTransaction" label="Average Transaction" keyboardType="numeric" />
      <FormTextField control={control} name="primarySupplier" label="Primary Supplier (optional)" />

      <PrimaryButton onPress={handleSubmit(onNext)} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
"""

FILES["app/(business)/profile-setup/step-4-documents.tsx"] = r"""import React from "react";
import { StyleSheet, View } from "react-native";
import { Text, List } from "react-native-paper";
import { useRouter } from "expo-router";
import { IdCard, Images, Receipt, Landmark } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { AppCard } from "@/components/cards/AppCard";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 4 - Documents.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 4)
 * and docs/04_DATABASE_DESIGN.txt Section 4.2 (business_documents) /
 * Section 4.6 (verification_documents).
 *
 * Document upload (image picker) integration is stubbed here with
 * placeholder rows; wire up an image picker + businessApi.uploadDocument
 * in the next implementation pass.
 */
export default function DocumentsStep() {
  const router = useRouter();

  const onNext = () => {
    router.push("/(business)/profile-setup/step-5-review");
  };

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={4} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Documents
      </Text>

      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="ID Copy" description="Required" left={() => <IdCard size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Business Photos" description="Required" left={() => <Images size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Trading Proof" description="Required" left={() => <Receipt size={22} />} />
      </AppCard>
      <AppCard style={{ marginBottom: spacing.md }}>
        <List.Item title="Bank Statement" description="Optional" left={() => <Landmark size={22} />} />
      </AppCard>

      <View style={{ flex: 1 }} />

      <PrimaryButton onPress={onNext} style={{ marginTop: spacing.md }}>
        Continue
      </PrimaryButton>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
});
"""

FILES["app/(business)/profile-setup/step-5-review.tsx"] = r"""import React from "react";
import { StyleSheet, ScrollView, View } from "react-native";
import { Text, Divider } from "react-native-paper";
import { useRouter } from "expo-router";
import { useMutation } from "@tanstack/react-query";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ProgressStepper } from "@/components/ui/ProgressStepper";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { AppCard } from "@/components/cards/AppCard";
import { LoadingOverlay } from "@/components/feedback/LoadingOverlay";
import { useBusinessProfileWizard } from "@/features/business/hooks/useBusinessProfileWizard";
import { businessApi } from "@/features/business/api/businessApi";
import { spacing } from "@/theme/spacing";

const STEP_LABELS = ["Business Info", "Owner Info", "Trading Info", "Documents", "Review"];

/**
 * Step 5 - Review & Submit.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Step 5)
 * and docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.2
 * (PUT /businesses/me).
 */
export default function ReviewStep() {
  const router = useRouter();
  const wizard = useBusinessProfileWizard();

  const submit = useMutation({
    mutationFn: () => businessApi.submitProfileSetup(wizard),
    onSuccess: () => {
      wizard.reset();
      router.replace("/(dashboard)/home");
    },
  });

  return (
    <ScreenContainer>
      <ScreenHeader onBack={() => router.back()} />
      <ProgressStepper totalSteps={5} currentStep={5} stepLabels={STEP_LABELS} />
      <Text variant="headlineSmall" style={styles.title}>
        Review Your Information
      </Text>

      <ScrollView showsVerticalScrollIndicator={false}>
        <ReviewSection title="Business Information">
          <ReviewRow label="Business Name" value={wizard.businessInfo.businessName} />
          <ReviewRow label="Trading Name" value={wizard.businessInfo.tradingName} />
          <ReviewRow label="Business Type" value={wizard.businessInfo.businessType} />
          <ReviewRow label="Industry" value={wizard.businessInfo.industry} />
          <ReviewRow label="Years Operating" value={wizard.businessInfo.yearsOperating} />
          <ReviewRow label="Address" value={wizard.businessInfo.addressLine} />
        </ReviewSection>

        <ReviewSection title="Owner Information">
          <ReviewRow label="Owner Name" value={wizard.ownerInfo.ownerName} />
          <ReviewRow label="ID Number" value={wizard.ownerInfo.saIdNumber} />
          <ReviewRow label="Phone" value={wizard.ownerInfo.phoneNumber} />
          <ReviewRow label="Email" value={wizard.ownerInfo.email} />
        </ReviewSection>

        <ReviewSection title="Trading Information">
          <ReviewRow label="Monthly Revenue" value={wizard.tradingInfo.monthlyRevenue} />
          <ReviewRow label="Customers Per Month" value={wizard.tradingInfo.customersPerMonth} />
          <ReviewRow label="Average Transaction" value={wizard.tradingInfo.averageTransaction} />
          <ReviewRow label="Primary Supplier" value={wizard.tradingInfo.primarySupplier} />
        </ReviewSection>
      </ScrollView>

      {submit.isError && (
        <Text style={styles.errorText}>
          We couldn't submit your profile. Please check your connection and try again.
        </Text>
      )}

      <PrimaryButton
        onPress={() => submit.mutate()}
        loading={submit.isPending}
        style={{ marginTop: spacing.md }}
      >
        Submit
      </PrimaryButton>

      <LoadingOverlay visible={submit.isPending} label="Submitting your profile..." />
    </ScreenContainer>
  );
}

function ReviewSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <AppCard style={{ marginBottom: spacing.md }}>
      <Text variant="titleMedium" style={{ fontWeight: "700", marginBottom: spacing.sm }}>
        {title}
      </Text>
      <Divider style={{ marginBottom: spacing.sm }} />
      {children}
    </AppCard>
  );
}

function ReviewRow({ label, value }: { label: string; value?: string }) {
  return (
    <View style={styles.reviewRow}>
      <Text style={styles.reviewLabel}>{label}</Text>
      <Text style={styles.reviewValue}>{value || "-"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  title: { fontWeight: "700", marginVertical: spacing.lg },
  reviewRow: { flexDirection: "row", justifyContent: "space-between", marginBottom: spacing.xs },
  reviewLabel: { opacity: 0.6 },
  reviewValue: { fontWeight: "600" },
  errorText: { color: "#D64545", marginTop: spacing.sm },
});
"""

FILES["app/(dashboard)/_layout.tsx"] = r"""import { Stack } from "expo-router";

export default function DashboardLayout() {
  return <Stack screenOptions={{ headerShown: false }} />;
}
"""

FILES["app/(dashboard)/home.tsx"] = r"""import React from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { Text, Avatar } from "react-native-paper";
import { Receipt, UserPlus, ShieldCheck } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppCard } from "@/components/cards/AppCard";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { EmptyState } from "@/components/feedback/EmptyState";
import { ErrorState } from "@/components/feedback/ErrorState";
import { useBusinessDashboard } from "@/features/dashboard/hooks/useBusinessDashboard";
import { spacing } from "@/theme/spacing";

/**
 * Home Dashboard (foundation for Phase 1).
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Business Dashboard)
 * and docs/07_DATA_AND_TRUST_ENGINE.txt (Business Trust Score /
 * business_health_scores).
 *
 * Full dashboard composition (Today's Orders, Nearby Suppliers,
 * Recommended Products, Recent Activity Timeline) is scoped for the next
 * phase of screens; this establishes the route, data-fetching pattern, and
 * Quick Actions used by later phases.
 */
export default function HomeDashboard() {
  const { data, isLoading, isError, refetch } = useBusinessDashboard();

  if (isError) return <ErrorState onRetry={() => refetch()} />;

  return (
    <ScreenContainer>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text variant="bodyMedium" style={{ opacity: 0.6 }}>
              Welcome back,
            </Text>
            <Text variant="headlineSmall" style={{ fontWeight: "700" }}>
              {data?.businessName ?? "Your Business"}
            </Text>
          </View>
          <Avatar.Text size={44} label="TC" />
        </View>

        <AppCard style={{ marginTop: spacing.lg }}>
          <Text variant="bodySmall" style={{ opacity: 0.6 }}>
            Business Trust Score
          </Text>
          <Text variant="displaySmall" style={{ fontWeight: "700", marginTop: spacing.xs }}>
            {isLoading ? "..." : data?.trustScore ?? "--"}
          </Text>
          <Text variant="bodySmall" style={{ opacity: 0.6, marginTop: spacing.xs }}>
            Builds automatically as you trade -- see
            docs/07_DATA_AND_TRUST_ENGINE.txt
          </Text>
        </AppCard>

        <View style={styles.row}>
          <AppCard style={styles.halfCard}>
            <Text style={{ opacity: 0.6 }}>Today's Sales</Text>
            <Text variant="titleLarge" style={{ fontWeight: "700" }}>
              {isLoading ? "..." : data?.todaySales ?? "R0"}
            </Text>
          </AppCard>
          <AppCard style={styles.halfCard}>
            <Text style={{ opacity: 0.6 }}>Trading Activity</Text>
            <Text variant="titleLarge" style={{ fontWeight: "700" }}>
              {isLoading ? "..." : data?.tradingActivityCount ?? 0}
            </Text>
          </AppCard>
        </View>

        <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.lg }}>
          Quick Actions
        </Text>
        <View style={[styles.row, { gap: spacing.sm }]}>
          <FeatureTile label="Upload Receipts" icon={<Receipt size={22} />} />
          <FeatureTile label="Add Supplier" icon={<UserPlus size={22} />} />
          <FeatureTile label="Verify Information" icon={<ShieldCheck size={22} />} />
        </View>

        <Text variant="titleMedium" style={{ fontWeight: "700", marginTop: spacing.lg }}>
          Recent Activity
        </Text>
        <View style={{ marginTop: spacing.sm, marginBottom: spacing.xl }}>
          <EmptyState message="No activity yet. Once you start trading, your activity timeline appears here." />
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: spacing.lg,
  },
  row: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.md },
  halfCard: { flex: 1 },
});
"""


# ==============================================================================
# MERGE HELPERS -- read existing config files, add only what TRU Connect
# needs, write back. Never remove or downgrade something already there.
# ==============================================================================

def _read_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def merge_package_json(path: str) -> list:
    """Merge required deps/devDeps/scripts into an existing package.json.
    Returns a list of human-readable change descriptions."""
    changes = []
    data = _read_json(path)

    if data.get("main") != "expo-router/entry":
        data["main"] = "expo-router/entry"
        changes.append('set "main": "expo-router/entry" (required by Expo Router)')

    data.setdefault("dependencies", {})
    for dep, version in REQUIRED_DEPENDENCIES.items():
        if dep not in data["dependencies"]:
            data["dependencies"][dep] = version
            changes.append(f"added dependency {dep}@{version}")

    data.setdefault("devDependencies", {})
    for dep, version in REQUIRED_DEV_DEPENDENCIES.items():
        if dep not in data["devDependencies"]:
            data["devDependencies"][dep] = version
            changes.append(f"added devDependency {dep}@{version}")

    data.setdefault("scripts", {})
    for name, command in REQUIRED_SCRIPTS.items():
        if name not in data["scripts"]:
            data["scripts"][name] = command
            changes.append(f'added script "{name}"')

    if changes:
        _write_json(path, data)
    return changes


def merge_app_json(path: str) -> list:
    """Merge additive TRU Connect config into an existing app.json, leaving
    existing icon/splash/adaptive-icon asset paths completely untouched."""
    changes = []
    data = _read_json(path)
    expo = data.setdefault("expo", {})

    if "scheme" not in expo:
        expo["scheme"] = "truconnect"
        changes.append('added "scheme": "truconnect"')

    plugins = expo.setdefault("plugins", [])

    def _plugin_present(name: str) -> bool:
        for p in plugins:
            if p == name or (isinstance(p, list) and p and p[0] == name):
                return True
        return False

    if not _plugin_present("expo-router"):
        plugins.append("expo-router")
        changes.append('added "expo-router" to plugins')

    extra = expo.setdefault("extra", {})
    if "apiBaseUrl" not in extra:
        extra["apiBaseUrl"] = "https://api.truconnect.dev/api/v1"
        changes.append('added extra.apiBaseUrl')

    if changes:
        _write_json(path, data)
    return changes


def merge_tsconfig(path: str) -> list:
    changes = []
    data = _read_json(path)
    compiler_options = data.setdefault("compilerOptions", {})

    if "baseUrl" not in compiler_options:
        compiler_options["baseUrl"] = "."
        changes.append('set compilerOptions.baseUrl "."')

    paths = compiler_options.setdefault("paths", {})
    if "@/*" not in paths:
        paths["@/*"] = ["src/*"]
        changes.append('added compilerOptions.paths "@/*" -> "src/*"')

    include = data.setdefault("include", [])
    for entry in ("src", "app"):
        if entry not in include:
            include.append(entry)
            changes.append(f'added "{entry}" to include')

    if changes:
        _write_json(path, data)
    return changes


def merge_gitignore(path: str) -> list:
    changes = []
    with open(path, "r", encoding="utf-8") as f:
        existing_lines = {line.strip() for line in f.readlines()}

    missing = [line for line in REQUIRED_GITIGNORE_LINES if line not in existing_lines]
    if missing:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n# --- TRU Connect additions ---\n")
            for line in missing:
                f.write(line + "\n")
        changes = [f"appended {len(missing)} missing entrie(s)"]
    return changes


# ==============================================================================
# GENERATION LOGIC
# ==============================================================================

# Config files that are MERGED (not overwritten) when they already exist.
# Maps relative-to-mobile path -> merge function.
MERGEABLE_CONFIG_FILES = {
    "package.json": merge_package_json,
    "app.json": merge_app_json,
    "tsconfig.json": merge_tsconfig,
    ".gitignore": merge_gitignore,
}

# Files that are only ever created if missing, never modified once present.
CREATE_IF_MISSING_ONLY = {
    "babel.config.js",
    "README.md",
}


def find_legacy_files(mobile_dir: str) -> list:
    found = []
    for rel_path in LEGACY_MOBILE_PATHS:
        full_path = os.path.join(mobile_dir, rel_path)
        if os.path.exists(full_path):
            found.append(rel_path)
    return found


def remove_legacy_files(mobile_dir: str, legacy_paths: list) -> None:
    import shutil
    for rel_path in legacy_paths:
        full_path = os.path.join(mobile_dir, rel_path)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        print(f"   removed: {rel_path}")


def ensure_root_scaffold(root_dir: str) -> None:
    """Create root-level monorepo folders/docs if missing. Never touches
    anything that already exists at the root, aside from writing the 10
    doc files into docs/ (which this generator fully owns)."""
    for rel_dir in ROOT_PLACEHOLDER_DIRS:
        full_dir = os.path.join(root_dir, rel_dir)
        if not os.path.isdir(full_dir):
            os.makedirs(full_dir, exist_ok=True)
            print(f"   created directory: {rel_dir}/")

    docs_dir = os.path.join(root_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    for doc_name, doc_content in DOCS.items():
        with open(os.path.join(docs_dir, doc_name), "w", encoding="utf-8") as f:
            f.write(doc_content)
    print(f"   wrote {len(DOCS)} documentation file(s) to docs/")

    root_readme = os.path.join(root_dir, "README.md")
    if not os.path.isfile(root_readme):
        with open(root_readme, "w", encoding="utf-8") as f:
            f.write(ROOT_README_CONTENT)
        print("   created README.md")


def generate_mobile(mobile_dir: str, force: bool, clean: bool) -> None:
    os.makedirs(mobile_dir, exist_ok=True)

    written = 0
    merged = 0
    created_fresh = 0
    skipped = 0

    for rel_path, content in FILES.items():
        full_path = os.path.join(mobile_dir, rel_path)
        base_name = os.path.basename(rel_path)

        # 1) Mergeable shared config files.
        if rel_path in MERGEABLE_CONFIG_FILES:
            if os.path.isfile(full_path):
                try:
                    changes = MERGEABLE_CONFIG_FILES[rel_path](full_path)
                except (ValueError, KeyError) as exc:
                    print(f"   WARNING: could not parse existing {rel_path} ({exc}); leaving it untouched.")
                    skipped += 1
                    continue
                if changes:
                    merged += 1
                    print(f"   merged {rel_path}:")
                    for c in changes:
                        print(f"      - {c}")
                else:
                    print(f"   {rel_path} already up to date, no changes needed")
                continue
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                # File didn't exist a moment ago -- run the same merge
                # function now so required deps/settings actually get
                # populated instead of leaving the bare placeholder.
                MERGEABLE_CONFIG_FILES[rel_path](full_path)
                created_fresh += 1
                continue

        # 2) Create-if-missing-only files.
        if rel_path in CREATE_IF_MISSING_ONLY or base_name in CREATE_IF_MISSING_ONLY:
            if os.path.isfile(full_path):
                skipped += 1
                continue
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_fresh += 1
            continue

        # 3) Everything else (app/**, src/**, .env.example) is fully owned
        #    by this generator and written/overwritten every run.
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        written += 1

    print()
    print(f"   {written} file(s) written/overwritten (app/**, src/**)")
    print(f"   {merged} shared config file(s) merged")
    print(f"   {created_fresh} file(s) created fresh (did not exist before)")
    print(f"   {skipped} file(s) left untouched (already exist, not overwritten)")

    legacy = find_legacy_files(mobile_dir)
    if legacy:
        if clean:
            print()
            print("   Removing superseded default Expo scaffold files (--clean):")
            remove_legacy_files(mobile_dir, legacy)
        else:
            print()
            print("   NOTE: found default Expo scaffold item(s) superseded by the new")
            print("   app/ + src/ structure (left untouched -- re-run with --clean to remove):")
            for f in legacy:
                print(f"      - {f}")
            if os.path.exists(os.path.join(mobile_dir, "app", "(tabs)")):
                print("      IMPORTANT: app/(tabs)/index.tsx and the new app/index.tsx (splash)")
                print("      both resolve to the \"/\" route. Expo Router will not start reliably")
                print("      until you remove app/(tabs) (via --clean) or rename/relocate it.")


def print_plan(root_dir: str, mobile_dir: str) -> None:
    print("=" * 78)
    print(" TRU CONNECT - Phase 1 generation plan")
    print("=" * 78)
    print(f" Monorepo root:  {os.path.abspath(root_dir)}")
    print(f" Mobile target:  {os.path.abspath(mobile_dir)}")
    print()
    print(" Root-level:")
    print("   - ensure backend/, database/, deployment/, frontend/web/, scripts/ exist")
    print("   - write docs/00-09 (10 files, always overwritten -- generator-owned)")
    print("   - create README.md only if missing")
    print()
    print(" Mobile app (frontend/mobile):")
    print("   - WRITE  app/** and src/** (generator-owned, always overwritten)")
    print("   - MERGE  package.json, app.json, tsconfig.json, .gitignore")
    print("            (existing settings/scripts/asset paths preserved)")
    print("   - SKIP   .claude/, CLAUDE.md, AGENTS.md, eslint.config.js,")
    print("            package-lock.json, assets/images/**, expo-env.d.ts,")
    print("            README.md if it already exists")
    print("   - babel.config.js created only if missing")
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="Generate/update the TRU Connect Phase 1 mobile app inside a "
        "TRU_Connect monorepo, without destroying the existing project scaffold."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Path to the TRU_Connect monorepo root (default: current directory).",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Skip the confirmation prompt.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Also remove default Expo scaffold items superseded by the new "
        "structure: app/(tabs)/, app/modal.tsx, and the top-level demo "
        "components/, constants/, hooks/ folders. Does NOT touch "
        "node_modules, .git, .claude/, CLAUDE.md, AGENTS.md, "
        "eslint.config.js, package-lock.json, or assets/images/**.",
    )
    args = parser.parse_args()

    root_dir = args.root
    mobile_dir = os.path.join(root_dir, MOBILE_REL)

    print_plan(root_dir, mobile_dir)

    if not args.force:
        response = input("Proceed? [y/N]: ")
        if response.strip().lower() != "y":
            print("Aborted. Re-run with --force to skip this prompt next time.")
            sys.exit(1)

    print()
    print("Applying root-level scaffold...")
    ensure_root_scaffold(root_dir)

    print()
    print("Applying frontend/mobile changes...")
    generate_mobile(mobile_dir, force=args.force, clean=args.clean)

    print()
    print("=" * 78)
    print(" Done.")
    print("=" * 78)
    print(" Next steps:")
    print(f"   cd {mobile_dir}")
    print("   npm install")
    print("   npx expo install --fix   # reconcile dependency versions for SDK 54")
    print("   npx expo start")
    print()
    print(" Read docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt for the full spec.")
    print("=" * 78)


if __name__ == "__main__":
    main()