import mongoose from "mongoose";

const orderSchema = new mongoose.Schema(
  {
    buyerId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    buyer: {
      type: String,
      required: true,
      trim: true,
    },

    /**
     * ==========================================
     * ORDER PRODUCTS
     * ==========================================
     *
     * We save the product price at the moment
     * the buyer places the order.
     *
     * This protects the order if the seller
     * changes the marketplace price later.
     */

    products: [
      {
        productId: {
          type: mongoose.Schema.Types.ObjectId,
          ref: "Marketplace",
          required: true,
        },

        sellerId: {
          type: mongoose.Schema.Types.ObjectId,
          ref: "User",
          required: true,
        },

        title: {
          type: String,
          required: true,
          trim: true,
        },

        priceAtPurchase: {
          type: Number,
          required: true,
          min: 0,
        },

        quantity: {
          type: Number,
          required: true,
          min: 1,
          default: 1,
        },

        subtotal: {
          type: Number,
          required: true,
          min: 0,
        },

        currency: {
          type: String,
          enum: ["RWF", "USD"],
          required: true,
        },
      },
    ],

    /**
     * ==========================================
     * ORDER TOTAL
     * ==========================================
     */

    total: {
      type: Number,
      required: true,
      min: 0,
    },

    /**
     * ==========================================
     * DELIVERY
     * ==========================================
     */

    deliveryAddress: {
      type: String,
      required: true,
      trim: true,
    },

    /**
     * ==========================================
     * PAYMENT METHOD
     * ==========================================
     */

    paymentMethod: {
      type: String,
      required: true,
      trim: true,
    },

    /**
     * ==========================================
     * ORDER STATUS
     * ==========================================
     */

    status: {
      type: String,
      enum: [
        "Pending",
        "Accepted",
        "Rejected",
        "Shipped",
        "Delivered",
        "Completed",
        "Cancelled",
      ],
      default: "Pending",
    },

    /**
     * ==========================================
     * PAYMENT STATUS
     * ==========================================
     */

    paymentStatus: {
      type: String,
      enum: [
        "Pending",
        "Paid",
        "Failed",
        "Refunded",
      ],
      default: "Pending",
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model(
  "Order",
  orderSchema
);