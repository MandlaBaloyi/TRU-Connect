MASTER PROMPT — TRU Connect Dashboard Architecture (Version 1.0)
Objective

You are continuing development of TRU Connect, the mobile application that forms the data collection and business operating layer of the TruePoint ecosystem.

This dashboard is NOT a simple home page.

It is the primary operational workspace where businesses and suppliers spend most of their time.

The dashboard architecture must therefore be:

scalable
modular
reusable
algorithm-ready
API-ready
AI-ready

Everything must align with the following documentation:

00_PROJECT_VISION.txt
01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt
02_SYSTEM_UI_UX_SPECIFICATION.txt
03_FRONTEND_COMPONENT_SPECIFICATION.txt
04_DATABASE_DESIGN.txt
05_BACKEND_API_SPECIFICATION.txt
06_BUSINESS_RULES_AND_WORKFLOWS.txt
07_DATA_AND_TRUST_ENGINE.txt
08_PRODUCT_ROADMAP.txt
09_ECOSYSTEM_STRATEGY.txt

Do not redesign workflows outside these specifications.

Dashboard Philosophy

TRU Connect is not a banking app.

It is a Business Operating Platform.

The dashboard must feel like the operational control centre of a business.

Users should immediately understand:

what is happening today
what needs attention
what actions they can perform
where the business is growing
how their Trust Score is improving

The interface should prioritise:

speed
clarity
minimal navigation
card-based layouts
touch-friendly interactions
progressive disclosure
offline-first behaviour
There are TWO completely different dashboards

Business Users and Suppliers are different users.

They must never share the same dashboard.

Business User

Purpose

Buy stock.

Trade.

Build Trust Score.

Access financing.

Dashboard focus

Business overview

Today's trading

Suppliers

Orders

Receipts

Trust Score

Trading history

Recommendations

Financing

Notifications

Supplier User

Purpose

Sell products.

Receive orders.

Manage customers.

Manage inventory.

Grow revenue.

Dashboard focus

Incoming orders

Deliveries

Products

Inventory

Customers

Analytics

Revenue

Catalogue

Performance

Notifications

Never merge these dashboards.

Only reusable UI components may be shared.

Approved Folder Structure
app
└── (dashboard)

      business
          home.tsx

      supplier
          home.tsx
features/dashboard

    business

        api

        hooks

        components

        types

    supplier

        api

        hooks

        components

        types

    shared

Shared contains only reusable dashboard components.

Examples

DashboardHeader
StatCard
AnalyticsCard
FeatureTile
QuickActionCard
SectionHeader
NotificationCard
LoadingState
EmptyState
ErrorState

Business-specific code must never live inside supplier folders.

Supplier-specific code must never live inside business folders.

Business Dashboard Features
Header

Good Morning Mandla

Business Name

Notification icon

Profile avatar

Business Trust Score

Display

Current score

Trend

Progress

Future integration

Trust Engine

Behaviour Engine

Credit Engine

Quick Actions

Find Suppliers

Upload Receipt

Add Supplier

Track Orders

Verify Business

Request Financing

Today's Snapshot

Orders This Month

Total Purchases

Active Suppliers

Current Trust Score

Trading Activity

Nearby Suppliers

Future APIs

Google Maps API

OpenStreetMap

Geoapify

Card examples

Makro

Boxer Wholesale

Verified Supplier

Local Distributor

Recommended Products

Future recommendation engine

Frequently Purchased Together

Top Sellers

Category Recommendations

Seasonal Products

Examples

Rice

Cooking Oil

Bread Flour

Cold Drinks

Sugar

Recent Activity Timeline

Receipt Uploaded

Order Submitted

Supplier Added

Trust Score Increased

Verification Approved

Financing Opportunities

Future integration

TRU Wallet

TruePoint

Partner Lenders

Cards

Eligible for Stock Finance

Pre-qualified

Requires More Trading History

Credit Limit Available

Supplier Dashboard Features
Header

Welcome Back

Supplier Name

Notifications

Profile

Quick Actions

Add Product

Upload Catalogue

Manage Orders

Manage Deliveries

Customer Requests

View Analytics

Business Overview

Products Listed

Orders Received

Businesses Served

Revenue

Pending Deliveries

Incoming Orders

Pending

Accepted

Packed

Dispatched

Delivered

Cancelled

Customer Activity

New Businesses

Repeat Customers

Top Customers

Recent Orders

Analytics

Future algorithms

Top Products

Revenue Trend

Fastest Moving Stock

Customer Growth

Sales Trend

Delivery Performance

Dashboard Algorithms

Dashboards must not simply display database values.

They must prepare for business algorithms.

Business Algorithms

Trading Frequency

Monthly Revenue

Purchase Trends

Supplier Frequency

Receipt Consistency

Trust Growth

Business Activity

Daily Streaks

Business Growth

Financing Readiness

Supplier Algorithms

Sales Trends

Top Products

Revenue Growth

Customer Retention

Delivery Performance

Order Completion

Fast Moving Products

Inventory Alerts

Repeat Customers

Search Algorithms

Supplier Search

Normalize text

Fuzzy search

Distance ranking

Trust ranking

Rating ranking

Inventory ranking

Delivery ranking

Return best suppliers

Product Search

Category ranking

Popularity

Availability

Supplier Trust

Distance

Search relevance

Recommendation Algorithms

Business Category

Purchase History

Seasonality

Nearby Demand

Supplier Ratings

Inventory

Trading Behaviour

Return recommended suppliers and products.

Trust Engine Integration

Already defined in

07_DATA_AND_TRUST_ENGINE.txt

The dashboard must reserve components for

Business Trust Score

Supplier Quality Score

Behaviour Indicators

Verification Status

Risk Indicators

Profile Completion

These calculations will later consume behavioural data collected throughout TRU Connect.

External API Ready

The architecture must already reserve integration points.

Maps

Google Maps

OpenStreetMap

Geoapify

Purpose

Nearby Suppliers

Business Location

Delivery Radius

Address Verification

Search

Algolia

Meilisearch

ElasticSearch

Purpose

Supplier Search

Product Search

Catalogue Search

Messaging

Twilio

WhatsApp Business API

Firebase Cloud Messaging

Purpose

Notifications

OTP

Order Updates

Supplier Alerts

Delivery Updates

Barcode APIs

Future

Product Lookup

Inventory

Catalogues

Weather APIs

Future

Agriculture

Delivery Planning

AI Ready Architecture

No AI implementation yet.

Reserve architecture for

Supplier Recommendation Agent

Business Assistant

Document Verification Agent

Risk Agent

Search Ranking Agent

Inventory Recommendation Agent

These will integrate after the dashboard foundation is complete.

Development Roadmap
Phase 1

Dashboard Foundation

Business dashboard

Supplier dashboard

Statistics cards

Quick actions

Notifications

Recent activity

Offline caching

Phase 2

Business Operations

Supplier Search

Product Catalogue

Orders

Receipts

Deliveries

Customer Requests

Phase 3

Smart Features

Recommendations

Trust Score

Analytics

Behaviour Metrics

Search Ranking

Phase 4

Intelligence

TruePoint Trust Engine

TruePoint Risk Engine

Predictive Insights

Supplier Recommendation Engine

AI Business Assistant

Development Rules

Every new dashboard feature must:

follow the approved folder structure
remain modular
support future external APIs
support future algorithms
support offline-first design
support React Query caching
support Zustand state where appropriate
be reusable where possible
never mix Business and Supplier workflows
align with all project documentation

The objective is to build a production-grade business operating platform rather than a collection of screens.

I would make one addition to this before any code is written.

Instead of just having:

features/dashboard/
    business/
    supplier/
    shared/

I'd also create:

features/dashboard/

    business/
        api/
        hooks/
        components/
        algorithms/
        services/
        types/

    supplier/
        api/
        hooks/
        components/
        algorithms/
        services/
        types/

    shared/
        components/
        hooks/
        utils/
        types/