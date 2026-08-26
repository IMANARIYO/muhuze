import { processPayment } from "../payment";
import { BUSINESS_SETTINGS } from "../settings";

import {
  requiresUploadFee,
  canUploadProduct,
} from "../rules/uploadRules";

import type { User } from "../../types/user";

export class UploadService {
  upload(user: User) {
    if (!canUploadProduct(user)) {
      throw new Error(
        "You are not allowed to upload products."
      );
    }

    if (requiresUploadFee(user)) {
      return processPayment({
        userId: user._id,

        service: "upload-fee",

        amount:
          BUSINESS_SETTINGS.services.uploadFee
            .price,

        referredBy: user.referredBy,
      });
    }

    return {
      success: true,

      message:
        "Premium seller. Upload fee waived.",

      commission: 0,
    };
  }
}