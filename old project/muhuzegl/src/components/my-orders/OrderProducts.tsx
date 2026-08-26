interface OrderProduct {
  _id?: string;
  productId?: string;

  item?: {
    _id?: string;
    title?: string;
    price?: number;
    image?: string;
    images?: string[];
  };

  quantity: number;
}

interface Props {
  products: OrderProduct[];
}

export default function OrderProducts({
  products,
}: Props) {
  return (
    <div className="mt-6">

      <h3 className="font-bold mb-3">
        Products
      </h3>

      <div className="space-y-3">

        {products.map(
          (product, index) => {

            const productId =
              product._id ||
              product.productId ||
              product.item?._id ||
              `product-${index}`;

            const title =
              product.item?.title ||
              "Product";

            return (
              <div
                key={productId}
                className="
                  flex
                  justify-between
                  items-center
                  gap-4
                "
              >

                <span>
                  {title}
                </span>

                <span className="font-semibold">
                  × {product.quantity}
                </span>

              </div>
            );
          }
        )}

      </div>

    </div>
  );
}