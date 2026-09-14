"""
The catalogue as a READABLE surface.

The catalogue has been write-only since it was built: supplier offers
resolve INTO it through the matching ladder and nothing ever reads back
out. It is maintained, reviewed and paid for, and returns nothing a user
can see.

This package is the half that makes it an asset -- browsing across every
supplier, and choosing WHICH supplier's offer a particular shop sees for
a product several of them carry. That second question is unaskable
without a resolved catalogue, which is exactly why it is the hard thing
to copy.
"""
