"""
Free tier metadata -- display/billing facts about the PLAN itself
(name, price), never a domain's own usage limits. Products' own limits
for Free live in products/tiers/free.py, not here -- this folder
answers "what is Free", not "what can Free do in Products".
"""
DISPLAY_NAME = "Free"
MONTHLY_PRICE_CENTS = 0
