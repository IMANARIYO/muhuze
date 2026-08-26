import mongoose from "mongoose";

const marketplaceSchema = new mongoose.Schema(
  {
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

    description: {
      type: String,
      required: true,
      trim: true,
    },

    marketplaceItemType: {
      type: String,
      enum: ["product", "rental", "service", "job"],
      required: true,
    },

    category: {
      type: String,
      required: true,
    },

    subCategory: {
      type: String,
      required: true,
    },

    images: [
      {
        type: String,
      },
    ],

    price: {
      type: Number,
      required: true,
    },

    oldPrice: {
      type: Number,
      default: null,
    },

    currency: {
      type: String,
      enum: ["RWF", "USD"],
      default: "RWF",
    },

    location: {
      type: String,
      required: true,
    },

    verified: {
      type: Boolean,
      default: false,
    },

    featured: {
      type: Boolean,
      default: false,
    },

    rating: {
      type: Number,
      default: 0,
    },

    reviews: {
      type: Number,
      default: 0,
    },

    status: {
      type: String,
      enum: [
        "draft",
        "published",
        "sold",
        "rented",
        "inactive",
      ],
      default: "published",
    },

    details: {
      type: mongoose.Schema.Types.Mixed,
      default: {},
    },
  },
  {
    timestamps: true,
  }
);

const Marketplace = mongoose.model(
  "Marketplace",
  marketplaceSchema
);

export default Marketplace;