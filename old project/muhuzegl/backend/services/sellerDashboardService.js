import Marketplace from "../models/Marketplace.js";
import Order from "../models/Order.js";

class SellerDashboardService {
  /**
   * Get seller dashboard statistics.
   */
  async getDashboardStats(sellerId) {
    /*
     * Get all listings belonging to this seller.
     */
    const listings = await Marketplace.find({
      sellerId,
    });

    /*
     * Get orders that contain products
     * belonging to this seller.
     */
    const orders = await Order.find()
      .populate(
        "products.item.sellerId",
        "fullName email phone"
      )
      .sort({
        createdAt: -1,
      });

    /*
     * Keep only orders containing
     * this seller's products.
     */
    const sellerOrders = orders.filter(
      (order) =>
        order.products.some((product) => {
          /*
           * New orders:
           * sellerId is stored directly
           * inside the order product.
           */
          if (product.sellerId) {
            return (
              product.sellerId.toString() ===
              sellerId.toString()
            );
          }

          /*
           * Older orders:
           * sellerId exists inside
           * product.item.sellerId.
           */
          const itemSellerId =
            product.item?.sellerId;

          if (!itemSellerId) {
            return false;
          }

          if (
            typeof itemSellerId === "object" &&
            itemSellerId._id
          ) {
            return (
              itemSellerId._id.toString() ===
              sellerId.toString()
            );
          }

          return (
            itemSellerId.toString() ===
            sellerId.toString()
          );
        })
    );

    /*
     * Listing statistics.
     */
    const totalListings =
      listings.length;

    const activeListings =
      listings.filter(
        (item) =>
          item.status === "published"
      ).length;

    /*
     * Order statistics.
     */
    const totalOrders =
      sellerOrders.length;

    const pendingOrders =
      sellerOrders.filter(
        (order) =>
          order.status === "Pending"
      ).length;

    const acceptedOrders =
      sellerOrders.filter(
        (order) =>
          order.status === "Accepted"
      ).length;

    const rejectedOrders =
      sellerOrders.filter(
        (order) =>
          order.status === "Rejected"
      ).length;

    /*
     * Calculate seller revenue.
     *
     * IMPORTANT:
     * We calculate revenue from the
     * seller's own products, not the
     * entire order total.
     */
    const revenue =
      sellerOrders.reduce(
        (total, order) => {
          const sellerRevenue =
            order.products.reduce(
              (productTotal, product) => {
                let productSellerId =
                  product.sellerId;

                /*
                 * Support older orders.
                 */
                if (!productSellerId) {
                  productSellerId =
                    product.item?.sellerId;
                }

                if (
                  typeof productSellerId ===
                    "object" &&
                  productSellerId?._id
                ) {
                  productSellerId =
                    productSellerId._id;
                }

                if (
                  !productSellerId ||
                  productSellerId.toString() !==
                    sellerId.toString()
                ) {
                  return productTotal;
                }

                const price =
                  Number(
                    product.item?.price || 0
                  );

                const quantity =
                  Number(
                    product.quantity || 1
                  );

                return (
                  productTotal +
                  price * quantity
                );
              },
              0
            );

          /*
           * Only count accepted,
           * shipped, or delivered orders
           * as seller revenue.
           */
          if (
            [
              "Accepted",
              "Shipped",
              "Delivered",
            ].includes(order.status)
          ) {
            return (
              total + sellerRevenue
            );
          }

          return total;
        },
        0
      );

    return {
      totalListings,
      activeListings,
      totalOrders,
      pendingOrders,
      acceptedOrders,
      rejectedOrders,
      revenue,
    };
  }
}

export default new SellerDashboardService();