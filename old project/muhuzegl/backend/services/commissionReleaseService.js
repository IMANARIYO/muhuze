import ReferralCommission from "../models/ReferralCommission.js";
import walletService from "./walletService.js";

class CommissionReleaseService {

  /**
   * ==========================================
   * RELEASE AVAILABLE COMMISSIONS
   * ==========================================
   *
   * Finds pending commissions whose
   * availableAt time has been reached.
   */

  async releaseAvailableCommissions() {

    const now = new Date();

    const commissions =
      await ReferralCommission.find({
        status: "Pending",

        availableAt: {
          $lte: now,
        },
      });

    const released = [];

    for (const commission of commissions) {

      try {

        await walletService.makeCommissionAvailable(
          commission.referrer,
          commission.commissionAmount,
          commission._id
        );

        commission.status =
          "Available";

        await commission.save();

        released.push(commission);

      } catch (error) {

        console.error(
          `Failed to release commission ${commission._id}:`,
          error.message
        );

      }
    }

    return released;
  }
}

export default new CommissionReleaseService();