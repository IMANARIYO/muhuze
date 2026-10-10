# Products API

**Status:** implemented (`app/modules/products/`). Rules and rationale: [`docs/features/007_products.md`](../features/007_products.md).

All paths are under `/api/v1/products` and use the [standard envelope](response-format.md). Money is a decimal string (`"850000.00"`), in RWF.

## For buyers (no login)

| Method | Path | Purpose |
|---|---|---|
| GET | `` | Products on sale across every open shop |
| GET | `/{product_id}` | One product with its pictures, details, and shop |

**List parameters**

| Parameter | Meaning |
|---|---|
| `seller_id` | Only this shop |
| `category_id` | Only this category |
| `q` | Search the product name: contains, case-insensitive, 1 to 100 characters |
| `min_price`, `max_price` | Price range, inclusive |
| `sort` | `published_at`, `price`, `name`; prefix `-` for descending. Default `-published_at` (newest first) |
| `page`, `page_size` | Standard pagination |

A product that is not on sale right now, for any reason, returns `404 Product not found`.

## For the seller

Needs a login, the `product.manage` permission (every seller has it), and an **active** seller. Every path reaches only the caller's own products; another shop's product returns `404`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/mine` | Your products in any status. `status`, `category_id`, `q`, `sort`, `page`, `page_size` |
| POST | `` | Create a draft (201) |
| GET | `/mine/{product_id}` | One of your products, with `publish_blockers` |
| PATCH | `/mine/{product_id}` | Change it |
| DELETE | `/mine/{product_id}` | Delete a draft that was never published |
| POST | `/mine/{product_id}/publish` | Put it on sale (from `draft` or `archived`) |
| POST | `/mine/{product_id}/archive` | Take it off sale |
| POST | `/mine/{product_id}/images` | Add a picture: multipart form, field `file` (201) |
| PUT | `/mine/{product_id}/images/order` | Set the order of the pictures |
| DELETE | `/mine/{product_id}/images/{image_id}` | Remove a picture |

`/mine` sorts by `created_at`, `price`, or `name` (default `-created_at`).

**The usual flow**

```
POST /                      create the draft, with the attribute values you have
POST /mine/{id}/images      add at least one picture
GET  /mine/{id}             publish_blockers tells you what is still missing
POST /mine/{id}/publish     works once publish_blockers is empty
```

## For staff

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/moderation` | `product.moderate` | Every product in any status. Seller filters plus `seller_id` |
| GET | `/moderation/{product_id}` | `product.moderate` | Any product, as its seller entered it |
| POST | `/moderation/{product_id}/hide` | `product.moderate` | Hide it from buyers; its seller cannot publish it |
| POST | `/moderation/{product_id}/restore` | `product.moderate` | Undo a hide |

## Bodies

**Create** (`PATCH` takes any subset):

```json
{
  "name": "Galaxy S24",
  "description": "Brand new, sealed.",
  "price": "850000",
  "category_id": "5d2c…",
  "attributes": {
    "storage": 256,
    "colour": "0a44…",
    "features": ["71f0…", "c2be…"],
    "refurbished": false,
    "model": "SM-S921"
  }
}
```

| Field | Rule |
|---|---|
| `name` | 1 to 200 characters |
| `description` | Optional, up to 20,000 characters |
| `price` | More than 0, at most two decimal places. Send as a string |
| `category_id` | One of your own categories. Changing it drops the attribute values |
| `attributes` | Keyed by attribute `code` (from the [category](categories.md)) |

**Attribute values by type**

| `data_type` | Send |
|---|---|
| `text` | a string |
| `number` | a JSON number |
| `boolean` | `true` or `false` |
| `select` | the **id** of one option |
| `multi_select` | a list of option ids |

In `PATCH`, only the codes sent are changed; `null` clears one. If any value is wrong, nothing is saved and the message lists every problem:

```
storage: must be a number; colour: must be one of this attribute's options (send the option id)
```

**Image order:** `{ "image_ids": ["…", "…"] }` with every image of the product exactly once. The first becomes the main picture.

## Responses

**Product** (buyer's page, seller's view, staff view):

```json
{
  "id": "e41a…",
  "seller_id": "3f0c…",
  "category_id": "5d2c…",
  "name": "Galaxy S24",
  "slug": "galaxy-s24",
  "price": "850000.00",
  "currency": "RWF",
  "status": "published",
  "main_image_url": "https://res.cloudinary.com/…/abc.jpg",
  "published_at": "2026-10-07T09:00:00Z",
  "hidden_by_staff_at": null,
  "created_at": "2026-10-07T08:40:00Z",
  "description": "Brand new, sealed.",
  "images": [
    { "id": "9c3d…", "url": "https://res.cloudinary.com/…/abc.jpg", "width": 1200, "height": 900, "sort_order": 0 }
  ],
  "attributes": [
    { "code": "storage", "name": "Storage", "data_type": "number", "unit": "GB", "value": 256 },
    { "code": "colour", "name": "Colour", "data_type": "select", "unit": null, "value": { "id": "0a44…", "value": "Black" } },
    { "code": "features", "name": "Features", "data_type": "multi_select", "unit": null, "value": [ { "id": "71f0…", "value": "NFC" } ] }
  ]
}
```

- **The buyer's page** adds `"shop": { "id": "3f0c…", "name": "Amina Shop" }` and shows only active attributes.
- **The seller's view** adds `"publish_blockers": ["Missing required attribute: Storage", "Add at least one image"]`, empty when the product is ready.
- **List items** have the fields down to `created_at` only (no description, images, or attributes).
- Attribute numbers are plain JSON numbers (they are measurements). Only `price` is a string.

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | Seller and staff endpoints without a token |
| 403 | `You do not have permission to perform this action` | Not a seller, or staff endpoint without the permission |
| 403 | `Only an approved, active seller can do this` | The seller is suspended, closed, or not approved |
| 404 | `Product not found` | Unknown id, **another shop's product**, or (for buyers) a product not on sale |
| 404 | `Category not found` | `category_id` is unknown or belongs to another shop |
| 404 | `Image not found` | Unknown image of your product |
| 409 | `This product is already published` / `Only a published product can be archived` | Status change not allowed |
| 409 | `This product was hidden by MUHUZE and cannot be published` | Publishing a hidden product |
| 409 | `A product that has been published cannot be deleted. Archive it instead.` | Deleting anything but a never-published draft |
| 422 | `Missing required attribute: Storage; Add at least one image` | Publishing, or an edit that would leave a published product incomplete |
| 422 | attribute problems, listed | Invalid `attributes` |
| 422 | `The image must be a JPEG or PNG` / `The image is larger than 5 MB` / `A product can have at most 8 images` | Image upload |
| 422 | `Send every image of the product exactly once` | Image order |
| 422 | field errors | Request validation |
| 503 | `File storage is not available right now. Please try again later.` | Storage not configured or unreachable |

Deleting a category, attribute, or option that products use returns `409` from the [categories API](categories.md).
