# Attributes and Variants

## How the attribute system works

MUHUZE uses a category-driven attribute system. Attributes are not
invented by sellers — they are defined per category by admins. This
prevents the chaos of free-form product data.

## The three layers

```
ATTRIBUTE DEFINITION          "What can vary?"
       │
       ▼
CATEGORY-ATTRIBUTE BINDING    "What applies to this category?"
       │
       ▼
VARIANT ATTRIBUTE VALUE       "What is the actual value?"
```

### Layer 1: Attribute definitions (`attributes`)

Admin-managed definitions of what attributes exist in the system:

| name | slug | input_type | unit |
|---|---|---|---|
| Color | color | select | — |
| Size | size | select | — |
| RAM | ram | select | GB |
| Storage | storage | select | GB |
| Screen Size | screen-size | number | inches |
| Battery | battery | number | mAh |
| Material | material | select | — |
| Gender | gender | select | — |
| Weight | weight | number | kg |

These are global definitions. An attribute can be used by multiple
categories.

### Layer 2: Category-attribute binding (`category_attributes`)

Which attributes apply to which category, and how:

**Smartphones category:**

| attribute | is_required | is_variant | is_filterable |
|---|---|---|---|
| Brand | True | False | True |
| RAM | True | True | True |
| Storage | True | True | True |
| Screen Size | True | False | True |
| Battery | True | False | True |
| Color | True | True | True |

**Shoes category:**

| attribute | is_required | is_variant | is_filterable |
|---|---|---|---|
| Brand | True | False | True |
| Gender | True | False | True |
| Size | True | True | True |
| Color | True | True | True |
| Material | False | False | True |
| Sole Material | False | False | False |

**Clothing category:**

| attribute | is_required | is_variant | is_filterable |
|---|---|---|---|
| Brand | True | False | True |
| Gender | True | False | True |
| Size | True | True | True |
| Color | True | True | True |
| Material | False | False | True |

### Layer 3: Variant attribute values (`variant_attribute_values`)

The actual values that define a specific variant:

**Samsung Galaxy A15 / 256GB / Black:**

| attribute | value |
|---|---|
| Color | Black |
| Storage | 256GB |
| RAM | 8GB |

**Nike Air Force 1 / White / 42:**

| attribute | value |
|---|---|
| Color | White |
| Size | 42 |

## How variants are generated

When a product is created, variants are generated from the category's
variant attributes.

### Example: Smartphones

Variant attributes: Color, Storage, RAM

Available values:
- Color: Black, Blue
- Storage: 128GB, 256GB
- RAM: 4GB, 8GB

Generated variants (2 × 2 × 2 = 8):

| Color | Storage | RAM |
|---|---|---|
| Black | 128GB | 4GB |
| Black | 128GB | 8GB |
| Black | 256GB | 4GB |
| Black | 256GB | 8GB |
| Blue | 128GB | 4GB |
| Blue | 128GB | 8GB |
| Blue | 256GB | 4GB |
| Blue | 256GB | 8GB |

### Example: Shoes

Variant attributes: Color, Size

Available values:
- Color: White, Black
- Size: 40, 41, 42, 43

Generated variants (2 × 4 = 8):

| Color | Size |
|---|---|
| White | 40 |
| White | 41 |
| White | 42 |
| White | 43 |
| Black | 40 |
| Black | 41 |
| Black | 42 |
| Black | 43 |

## Attribute input types

| input_type | Description | Example |
|---|---|---|
| `select` | Dropdown/predefined values. Values come from variant attributes or product attribute values. | Color: "Black", "White", "Blue" |
| `text` | Free-form text. Used for non-variant, non-filterable attributes. | Model name: "Galaxy A15" |
| `number` | Numeric value, optionally with a unit. | Battery: "5000" (unit: mAh) |

## How filtering works

Because attributes are structured, buyers can filter:

```
GET /api/v1/products?category=smartphones&color=black&storage=256gb
```

The system joins:

1. `products` → `product_variants` → `variant_attribute_values`
2. Filter by attribute values
3. Check that at least one `seller_listings` is active for matching
   variants

This is why `is_filterable` exists on `category_attributes` — it tells the
search system which attributes to expose as filter options.

## The uniqueness rule

Two variants of the same product cannot have the same combination of
attribute values.

**Valid:**
- Variant A: Color=Black, Storage=256GB
- Variant B: Color=Blue, Storage=256GB
- Variant C: Color=Black, Storage=128GB

**Invalid (duplicate):**
- Variant A: Color=Black, Storage=256GB
- Variant B: Color=Black, Storage=256GB ← same combination

This is enforced at the application layer when creating variants. The
database unique constraint on `(variant_id, attribute_id)` prevents
duplicate attributes *within* a variant, but cross-variant uniqueness
within a product is a service-level check.

## Future: attribute value suggestions

When a seller selects "Color" as a variant attribute for a smartphone, the
system could suggest:

```
Popular values for Color in Smartphones:
- Black (used by 45 products)
- White (used by 38 products)
- Blue (used by 32 products)
- Gold (used by 28 products)
```

This helps standardize values and prevents:

- "black" vs "Black" vs "BLK" vs "Black Color"
- "128 GB" vs "128GB" vs "128 gb"

For v1, values are entered freely. Standardization is a future concern.
