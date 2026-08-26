import type { User } from "../../types/user";
import type { PremiumPlan } from "../../types/premium";

export class PremiumEngine {

  activate(
    user: User,
    plan: PremiumPlan
  ): User {

    const today = new Date();

    const expiry = new Date(today);

    if (plan.name === "Monthly") {
      expiry.setDate(expiry.getDate() + 30);
    } else {
      expiry.setDate(expiry.getDate() + 365);
    }

    return {
      ...user,

      premium: {
        active: true,

        plan,

        startDate: today.toISOString(),

        expiryDate: expiry.toISOString(),
      },
    };
  }

  deactivate(user: User): User {

    return {

      ...user,

      premium: {
  active: false,

  plan: null,

  startDate: "",

  expiryDate: "",
}

    };
  }

  isActive(user: User) {

    if (!user.premium.active)
      return false;

    if (!user.premium.expiryDate)
      return false;

    return (
      new Date(user.premium.expiryDate)
      > new Date()
    );
  }

  daysRemaining(user: User) {

    if (!user.premium.expiryDate)
      return 0;

    const remaining =
      new Date(
        user.premium.expiryDate
      ).getTime() - Date.now();

    return Math.max(
      0,
      Math.ceil(
        remaining /
          (1000 * 60 * 60 * 24)
      )
    );
  }

}