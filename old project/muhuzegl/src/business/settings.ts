export const BUSINESS_SETTINGS = {
  currency: "RWF",

  referralPercentage: 10,

  minimumWithdrawal: 10000,

  services: {
  premium: {
    monthly: {
      id: "premium-monthly",
      name: "Monthly Premium",
      price: 10000,
      duration: 30,
      commission: 10,
    },

    annual: {
      id: "premium-annual",
      name: "Annual Premium",
      price: 100000,
      duration: 365,
      commission: 10,
    },
  },

  uploadFee: {
    id: "upload-fee",
    name: "Product Upload Fee",
    price: 2000,
    commission: 10,
  },

  featuredProduct: {
    id: "featured-product",
    name: "Featured Product",
    price: 5000,
    commission: 10,
  },

  advertising: {
    starter: {
      id: "advertising-starter",
      name: "Starter Advertising",
      price: 10000,
      commission: 10,
    },

    standard: {
      id: "advertising-standard",
      name: "Standard Advertising",
      price: 25000,
      commission: 10,
    },

    premium: {
      id: "advertising-premium",
      name: "Premium Advertising",
      price: 50000,
      commission: 10,
    },
  },
}}