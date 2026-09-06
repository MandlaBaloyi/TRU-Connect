"""
storefront -- everything a BUSINESS sees of a SUPPLIER: the brand
profile's product showcase, the paginated stock catalogue, one product
in detail, and the gate on whether an order can be placed at all.

WHY ITS OWN PACKAGE: this all lived in a single catalog_service.py that
had grown to 443 lines holding four unrelated jobs, and the ranking half
is the half that keeps growing (best-selling, most-repurchased, and
whatever follows). Splitting it now means a new ranking signal touches
ranking.py alone rather than the module that also happens to own
pagination and the ordering gate.

  product_dto.py      the one enriched product shape all of these share
  catalog_service.py  browsing: categories, paginated list, related, one
  showcase_service.py the brand profile's category strips
  ranking.py          PURE ranking signals -- no DB, no Flask
  ordering_gate.py    can a business order from this supplier at all

RANKING.PY IS DELIBERATELY PURE -- functions over plain dicts, nothing
imported from Flask or SQLAlchemy. Whatever data a future signal needs
(order counts, repurchase history) is FETCHED by showcase_service and
PASSED IN. That keeps the algorithm itself testable in milliseconds and
independently of any database.
"""
