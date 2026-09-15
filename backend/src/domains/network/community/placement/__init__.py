"""
Where a supplier's plan is allowed to matter, and nowhere else.

ONE DOOR, DELIBERATELY. Everything about tiers -- the ladder, the
ceilings, the tolerance band, the ordering -- lives behind this package
so that "does money touch this?" is answerable by reading an import
list rather than by auditing a sort key.

NOTHING IN demand/ MAY IMPORT THIS, and nothing here may import
demand/. The demand engine answers what a shop NEEDS and must not be
able to see who is paying; this module answers who gets REACH and must
not be able to see what a shop needs. The feed composer sits between
them and is the only thing that knows both.

tests/architecture/test_placement_boundaries.py holds both directions.
"""
