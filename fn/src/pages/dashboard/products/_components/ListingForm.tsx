import { toast } from 'sonner'
import { typeLabels } from '@/lib/format'
import { isProductType, productTypes } from '@/types/product'
import { Field, FormDialog, SelectField } from '../../_components/FormDialog'
import { useListings, type StoredListing } from '../_data'

interface Props {
  /** A listing to edit, 'new' to create one, or null when closed. */
  target: StoredListing | 'new' | null
  /** Set for a seller: the listing belongs to this shop and the seller field is not shown. */
  shop?: string
  onClose: () => void
}

export function ListingForm({ target, shop, onClose }: Props) {
  const { add, update } = useListings()
  const listing = target === 'new' ? null : target

  function save(data: FormData) {
    const type = data.get('type')
    const values = {
      title: String(data.get('title')),
      type: isProductType(type) ? type : 'sale',
      category: String(data.get('category')),
      price: Number(data.get('price')),
      unit: String(data.get('unit')) || undefined,
      seller: shop ?? String(data.get('seller')),
      image: String(data.get('image')),
    }
    if (listing) update(listing.id, values)
    else add({ ...values, views: 0, uses: 0, active: true })
    toast.success(listing ? 'Listing updated' : 'Listing created')
  }

  return (
    <FormDialog
      open={target !== null}
      onClose={onClose}
      title={listing ? 'Edit listing' : 'New listing'}
      description="Sale items earn commission; rentals and services rely on subscriptions."
      onSubmit={save}
    >
      <Field label="Title" name="title" defaultValue={listing?.title} required />
      <div className="grid grid-cols-2 gap-4">
        <SelectField
          label="Type"
          name="type"
          defaultValue={listing?.type}
          options={productTypes.map((type) => ({ value: type, label: typeLabels[type].name }))}
        />
        <Field label="Category" name="category" defaultValue={listing?.category} required />
        <Field label="Price (RWF)" name="price" type="number" min={0} defaultValue={listing?.price} required />
        <Field label="Per (rentals, services)" name="unit" placeholder="month, day, session" defaultValue={listing?.unit} />
      </div>
      {!shop && <Field label="Seller" name="seller" defaultValue={listing?.seller} required />}
      <Field label="Image URL" name="image" type="url" defaultValue={listing?.image} />
    </FormDialog>
  )
}
