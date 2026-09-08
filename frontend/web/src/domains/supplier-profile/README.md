# `supplier-profile/`

The supplier's own settings: fulfilment terms, minimum order, collection
address, accepted payment methods, visibility controls, capabilities.

**Capabilities, not tiers.** There is no `SupplierTier` enum and there should
not be. "Tier" is really several independent axes that merely correlate —
a small supplier wanting digital-only is reasonable, and so is a large one
wanting approval for new customers. One enum makes both unrepresentable.

Ask "can this supplier do X", never "what tier is this supplier".
See V2_00 section 2.2.
