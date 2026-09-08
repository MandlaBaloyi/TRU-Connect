# `catalogue/`

Supplier offers and, later, the shared product catalogue.

Empty until the portal is built.

Two things to know before writing anything here:

**An Offer is not a Product.** A `SupplierOffer` is one supplier's offer of
one product: their price, their pack, their SKU, their stock. The catalogue
`Product` is the shared thing itself — brand, barcode, consumer unit.

**Pack size lives on the Offer.** The Product is the consumer unit
("Coca-Cola Original 2L"); how many are in a case is the supplier's decision.
That is what makes price-per-unit comparable across suppliers who pack
differently — see V2_00 section 2.1.
