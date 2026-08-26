import cron from "node-cron";
import referralCommissionAvailabilityService from "../services/referralCommissionAvailabilityService.js";

const startReferralCommissionJob = () => {
  // Run every minute
  cron.schedule("* * * * *", async () => {
    try {
      const processed =
        await referralCommissionAvailabilityService
          .processAvailableCommissions();

      if (processed.length > 0) {
        console.log(
          `✅ Processed ${processed.length} referral commission(s).`
        );
      }
    } catch (error) {
      console.error(
        "❌ Referral commission job error:",
        error.message
      );
    }
  });

  console.log(
    "⏰ Referral commission scheduler started."
  );
};

export default startReferralCommissionJob;