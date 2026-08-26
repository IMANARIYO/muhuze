import ReferralCommission from "../models/ReferralCommission.js";
import walletService from "./walletService.js";

class ReferralCommissionAvailabilityService {
  /**
   * ==========================================
   * MAKE COMMISSION AVAILABLE
   * ==========================================
   */

  async makeAvailable(commissionId) {
    const commission =
      await ReferralCommission.findById(
        commissionId
      );

    if (!commission) {
      throw new Error(
        "Referral commission not found."
      );
    }

    // Already available
    if (
      commission.status ===
      "Available"
    ) {
      return commission;
    }

    // Cannot process reversed/cancelled
    if (
      commission.status ===
        "Reversed" ||
      commission.status ===
        "Cancelled"
    ) {
      throw new Error(
        `Commission is ${commission.status}.`
      );
    }

    // Make sure availability date
    // has been reached.
    if (
      commission.availableAt &&
      commission.availableAt >
        new Date()
    ) {
      throw new Error(
        "Commission is not available yet."
      );
    }

    // ==========================================
    // MOVE MONEY INTO WALLET
    // ==========================================

    await walletService.makeCommissionAvailable(
      commission.referrer,
      commission.commissionAmount,
      commission._id
    );

    // ==========================================
    // UPDATE COMMISSION
    // ==========================================

    commission.status =
      "Available";

    await commission.save();

    return commission;
  }

  /**
   * ==========================================
   * PROCESS ALL AVAILABLE COMMISSIONS
   * ==========================================
   */

  async processAvailableCommissions() {
    const commissions =
      await ReferralCommission.find({
        status: "Pending",
        availableAt: {
          $lte: new Date(),
        },
      });

    const processed = [];

    for (
      const commission of commissions
    ) {
      try {
        const updated =
          await this.makeAvailable(
            commission._id
          );

        processed.push(updated);
      } catch (error) {
        console.error(
          `Failed to process commission ${commission._id}:`,
          error.message
        );
      }
    }

    return processed;
  }
}

export default new ReferralCommissionAvailabilityService();