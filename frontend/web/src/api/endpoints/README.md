# `endpoints/`

One file per backend domain, each exporting typed request functions.

```ts
// offers.ts
export const listOffers = () => api.get<Offer[]>("/supplier-discovery/products");
```

**Paths still say `products`, deliberately.** The backend renamed the model
to `SupplierOffer` in v2 step 1, but the routes and JSON keys were left
untouched because the mobile app is a shipped client calling them. Internal
names moved; the contract did not.

These functions are transport only. Caching, retries and React Query live in
`domains/`.
