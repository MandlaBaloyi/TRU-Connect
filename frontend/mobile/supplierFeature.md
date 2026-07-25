Then your project structure becomes
supplier

└── product-catalogue
    ├── algorithms
    ├── api
    │     └── productCatalogueApi.ts
    │
    ├── components
    │     ├── ProductCard.tsx
    │     ├── ProductImageUploader.tsx
    │     ├── ProductForm.tsx
    │     ├── ProductPriceCard.tsx
    │     ├── ProductStatusBadge.tsx
    │     ├── ProductCategorySelector.tsx
    │     ├── ProductSearchBar.tsx
    │     └── ProductFilterSheet.tsx
    │
    ├── hooks
    │     ├── useProducts.ts
    │     ├── useCreateProduct.ts
    │     ├── useUpdateProduct.ts
    │     ├── useDeleteProduct.ts
    │     └── useProductSearch.ts
    │
    ├── screens
    │     ├── ProductCatalogueScreen.tsx
    │     ├── ProductDetailsScreen.tsx
    │     ├── AddProductScreen.tsx
    │     ├── EditProductScreen.tsx
    │     ├── DraftProductsScreen.tsx
    │     └── ProductImagesScreen.tsx
    │
    ├── services
    │     ├── productValidation.ts
    │     ├── productMapper.ts
    │     ├── pricingCalculator.ts
    │     └── stockManager.ts
    │
    └── types.ts
Now let's align it with the backend

This is where I think we can improve the backend architecture as well.

Instead of thinking in terms of generic folders like:

models/
repositories/
schemas/

we think in terms of one feature.

The Product Catalogue feature will touch every backend layer.

src

api
    product_routes.py

models
    product.py
    product_image.py
    product_category.py

repositories
    product_repository.py

schemas
    product_schema.py

services
    product_service.py

utils

This follows the same feature through each backend layer, keeping everything cohesive.