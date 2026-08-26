import mongoose from "mongoose";

const wishlistSchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    itemId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Marketplace",
      required: true,
    },
  },
  {
    timestamps: true,
  }
);

// A user cannot save the same listing twice
wishlistSchema.index(
  { userId: 1, itemId: 1 },
  { unique: true }
);

const Wishlist = mongoose.model(
  "Wishlist",
  wishlistSchema
);

export default Wishlist;