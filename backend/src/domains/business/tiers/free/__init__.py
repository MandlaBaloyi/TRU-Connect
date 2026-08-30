"""
Free tier metadata -- display/billing facts about the PLAN itself
(name, price), never a domain's own usage limits. stock_order's own
spending limits for Free live in
domains/business/stock_order/tiers/free.py, not here -- this folder
answers "what is Free", not "what can Free do in stock_order". Mirrors
domains/supplier/tiers/free/__init__.py's own shape exactly.
"""
DISPLAY_NAME = "Free"
MONTHLY_PRICE_CENTS = 0
