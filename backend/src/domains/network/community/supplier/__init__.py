"""
THE WHOLESALER'S Community feed.

For a supplier, Community is a DEMAND SIGNAL: who is buying, who has
gone quiet, what is stopping me selling.

MAY NOT IMPORT community/business/. See the sibling package's docstring
for why this is enforced rather than trusted.

A NOTE FOR WHEN THE PIPELINE ARRIVES: business candidates are mostly
PRODUCTS and supplier candidates are mostly PEOPLE. Sharing the engine's
arranging, thinning and stability is worth it; making this feed look
like the other one is the thing V2_04 3.1 already rejected.
"""
