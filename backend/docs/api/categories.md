# Categories API

**Status:** implemented (`app/modules/categories/`). Rules and rationale: [`docs/features/006_categories.md`](../features/006_categories.md).

All paths are under `/api/v1` and use the [standard envelope](response-format.md). Each seller owns the categories of their own shop; there is no shared marketplace tree.

## For buyers (no login)

| Method | Path | Purpose |
|---|---|---|
| GET | `/sellers/{seller_id}/categories` | A shop's active categories, each with its active attributes and options. `page`, `page_size`. `404` if the shop isn't open |

Use the attributes with `is_filterable: true` to build the shop's filters.

## For the seller

Needs a login, the `category.manage` permission (every seller has it), and an **active** seller. Every path below reaches only the caller's own categories; another shop's category returns `404`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/categories/mine` | Your categories, active or not, in your order. `is_active`, `q`, `page`, `page_size` |
| POST | `/categories` | Add a category (201) |
| GET | `/categories/{category_id}` | One category with all its attributes and options |
| PATCH | `/categories/{category_id}` | Change name, description, order, or switch it on/off |
| DELETE | `/categories/{category_id}` | Remove it with its attributes |
| POST | `/categories/{category_id}/attributes` | Add an attribute (201) |
| PATCH | `/categories/{category_id}/attributes/{attribute_id}` | Change an attribute (not its type) |
| DELETE | `/categories/{category_id}/attributes/{attribute_id}` | Remove an attribute |
| POST | `…/attributes/{attribute_id}/options` | Add an option (201) |
| PATCH | `…/attributes/{attribute_id}/options/{option_id}` | Rename, reorder, or retire an option |
| DELETE | `…/attributes/{attribute_id}/options/{option_id}` | Remove an option |

`PATCH` changes only the fields sent. The option endpoints return the whole attribute with its updated options.

## For staff

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/categories` | `category.moderate` | Every shop's categories. `seller_id`, `is_active`, `q`, `page`, `page_size` |
| POST | `/categories/{category_id}/hide` | `category.moderate` | Hide a category; its seller cannot reactivate it |
| POST | `/categories/{category_id}/restore` | `category.moderate` | Undo a hide |

## Bodies

**Category**

```json
{ "name": "Phones & Tablets", "description": "Mobile devices", "sort_order": 0 }
```

`name`: 1 to 100 characters, unique within the shop ignoring letter case. `description`: optional, up to 500. `sort_order`: optional, 0 or more, lowest first. `PATCH` also accepts `is_active`.

**Attribute**

```json
{
  "name": "Colour",
  "data_type": "select",
  "is_required": true,
  "is_filterable": true,
  "sort_order": 1,
  "options": ["Black", "White", "Blue"]
}
```

| Field | Rule |
|---|---|
| `name` | 1 to 100 characters, unique within the category ignoring letter case |
| `data_type` | `text`, `number`, `boolean`, `select`, `multi_select`. **Cannot be changed later** |
| `unit` | Optional, for `number` only: `GB`, `kg`, `cm` |
| `is_required` | A product cannot be published without it. Default `false` |
| `is_filterable` | Offered to buyers as a filter. Default `false` |
| `options` | For `select` and `multi_select` only, on creation. Add more with the options endpoints |

`PATCH` accepts `name`, `unit`, `is_required`, `is_filterable`, `sort_order`, `is_active`.

**Option:** `{ "value": "Red" }`. `sort_order` is optional; without it the option goes last. `PATCH` accepts `value`, `sort_order`, `is_active`.

## Responses

**Category** (the list endpoints for the seller and staff omit `attributes`):

```json
{
  "id": "5d2c…",
  "seller_id": "3f0c…",
  "name": "Phones & Tablets",
  "slug": "phones-tablets",
  "description": "Mobile devices",
  "sort_order": 0,
  "is_active": true,
  "hidden_by_staff_at": null,
  "created_at": "2026-10-06T14:00:00Z",
  "attributes": [
    {
      "id": "b81e…",
      "code": "colour",
      "name": "Colour",
      "data_type": "select",
      "unit": null,
      "is_required": true,
      "is_filterable": true,
      "sort_order": 1,
      "is_active": true,
      "options": [
        { "id": "0a44…", "value": "Black", "sort_order": 0, "is_active": true }
      ]
    }
  ]
}
```

- `code` is the stable key of an attribute. It is made once from the first name and **never changes**, even when the attribute is renamed. Products will refer to attributes by it.
- `slug` changes when the category is renamed.
- `hidden_by_staff_at` is set when MUHUZE hid the category. Show the seller that it was hidden and cannot be switched back on.

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | Seller and staff endpoints without a token |
| 403 | `You do not have permission to perform this action` | Not a seller, or staff endpoint without the permission |
| 403 | `Only an approved, active seller can do this` | The seller is suspended, closed, or not approved yet |
| 404 | `Category not found` | Unknown id, **or a category of another shop** |
| 404 | `Attribute not found` / `Option not found` | Unknown id within your category |
| 404 | `Seller not found` | Public shop page of a shop that isn't open |
| 409 | `You already have a category with this name` | Create or rename |
| 409 | `This category already has an attribute with this name` | Create or rename |
| 409 | `This attribute already has this option` | Add or rename |
| 409 | `This category still has products. Move them or switch the category off.` | Deleting a category that has products |
| 409 | `Products already use this attribute. Switch it off instead.` | Deleting an attribute that products have values for |
| 409 | `Products already use this option. Switch it off instead.` | Deleting an option that products use |
| 409 | `This category was hidden by MUHUZE and cannot be reactivated` | The seller sets `is_active: true` on a hidden category |
| 422 | `Only select and multi_select attributes have options` | Adding an option to another type |
| 422 | `Only number attributes have a unit` | Setting a unit on another type |
| 422 | field errors | Request validation |
