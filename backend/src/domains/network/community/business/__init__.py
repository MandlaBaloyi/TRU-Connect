"""
THE SHOP'S Community feed.

For a business, Community is a MARKET: what can I buy, from whom, at
what price, near me.

MAY NOT IMPORT community/supplier/. The two feeds are different
products, not two views of one -- V2_04 3.1 names mirroring them as the
mistake that started V2: "a supplier does not shop. Handing them a For
You rail of other suppliers is symmetry mistaken for design."

The risk is not conceptual, it is FILENAMES: these two lived side by
side in services/ as business_sections.py and supplier_sections.py, and
with a pipeline and sources added to that flat folder somebody would
eventually import one into the other because the import looked
plausible. tests/architecture/test_feed_roles.py makes it impossible
rather than discouraged.
"""
