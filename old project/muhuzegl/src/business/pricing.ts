import { BUSINESS_SETTINGS } from "./settings";

export const Pricing = {
  monthlyPremium:
    BUSINESS_SETTINGS.services.premium.monthly.price,

  annualPremium:
    BUSINESS_SETTINGS.services.premium.annual.price,

  uploadFee:
    BUSINESS_SETTINGS.services.uploadFee.price,

  featuredProduct:
    BUSINESS_SETTINGS.services.featuredProduct.price,
};