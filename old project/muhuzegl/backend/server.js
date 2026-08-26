import "dotenv/config";

import startReferralCommissionJob from "./jobs/referralCommissionJob.js";

import connectDB from "./config/db.js";
import app from "./app.js";


const PORT = process.env.PORT || 5000;

const startServer = async () => {
  try {
    await connectDB();

    startReferralCommissionJob();

    app.listen(PORT, "0.0.0.0", () => {
      console.log(
        `✅ Server running on http://localhost:${PORT}`
      );
    });
  } catch (error) {
    console.error(
      "❌ Failed to start server:",
      error
    );

    process.exit(1);
  }
};

startServer();