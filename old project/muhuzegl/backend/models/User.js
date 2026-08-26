import mongoose from "mongoose";

const userSchema = new mongoose.Schema(
  {
    // ==========================================
    // BASIC USER INFORMATION
    // ==========================================

    fullName: {
      type: String,
      required: true,
      trim: true,
    },

    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
    },

    password: {
      type: String,
      required: true,
    },

    phone: {
      type: String,
      default: "",
      unique: true,
      trim: true,
    },

    // ==========================================
    // USER ROLE
    // ==========================================

    role: {
      type: String,
      enum: ["buyer", "seller", "admin"],
      default: "buyer",
    },

    // ==========================================
    // VERIFICATION
    // ==========================================

    isVerified: {
      type: Boolean,
      default: false,
    },

    isEmailVerified: {
      type: Boolean,
      default: false,
    },

    isPhoneVerified: {
      type: Boolean,
      default: false,
    },

    sellerVerified: {
      type: Boolean,
      default: false,
    },

    emailVerificationToken: {
      type: String,
      default: "",
    },

    emailVerificationExpires: {
      type: Date,
      default: null,
    },

    // ==========================================
    // PROFILE INFORMATION
    // ==========================================

    profileImage: {
      type: String,
      default: "",
    },

    bio: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // RWANDA LOCATION
    // ==========================================

    country: {
      type: String,
      default: "Rwanda",
      trim: true,
    },

    // ==========================================
    // PROVINCE / CITY
    // ==========================================

    province: {
      type: String,
      default: "",
      trim: true,
    },

    provinceId: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // DISTRICT
    // ==========================================

    district: {
      type: String,
      default: "",
      trim: true,
    },

    districtId: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // SECTOR
    // ==========================================

    sector: {
      type: String,
      default: "",
      trim: true,
    },

    sectorId: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // CELL
    // ==========================================

    cell: {
      type: String,
      default: "",
      trim: true,
    },

    cellId: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // VILLAGE
    // ==========================================

    village: {
      type: String,
      default: "",
      trim: true,
    },

    villageId: {
      type: String,
      default: "",
      trim: true,
    },

    // ==========================================
    // PREMIUM MEMBERSHIP
    // ==========================================
    //
    // This is the user's CURRENT Premium status.
    //
    // The complete subscription/payment history
    // will be stored in PremiumSubscription.
    //
    // Premium membership:
    //
    // Monthly = $10 / 30 days
    // Annual  = $100 / 365 days
    //
    // Premium seller commission = 7%
    // Basic seller commission   = 12%
    //
    // Premium referral eligibility does NOT
    // guarantee referral income.
    //

    premium: {
      active: {
        type: Boolean,
        default: false,
      },

      plan: {
        type: String,
        enum: [
          "Monthly",
          "Annual",
          null,
        ],
        default: null,
      },

      startDate: {
        type: Date,
        default: null,
      },

      expiryDate: {
        type: Date,
        default: null,
      },

      // ========================================
      // REFERRAL PARTICIPATION
      // ========================================

      referralCommissionEligible: {
        type: Boolean,
        default: false,
      },

      // ========================================
      // SELLER COMMISSION
      // ========================================
      //
      // This is a current-status snapshot.
      //
      // Basic   = 12%
      // Premium = 7%
      //
      // Backend business logic should still
      // verify the Premium status before
      // applying the rate.
      //

      sellerCommissionRate: {
        type: Number,
        default: 12,
        min: 0,
        max: 100,
      },
    },
  },
  {
    timestamps: true,
  }
);

const User = mongoose.model(
  "User",
  userSchema
);

export default User;