import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  PremiumPlan,
  PremiumSubscription,
} from "../types/premium";

interface PremiumContextType {
  subscription: PremiumSubscription;

  activatePremium: (
    plan: PremiumPlan
  ) => void;

  deactivatePremium: () => void;

  daysRemaining: number;
}

const PremiumContext = createContext<
  PremiumContextType | undefined
>(undefined);

interface Props {
  children: ReactNode;
}

const defaultSubscription: PremiumSubscription = {
  active: false,
  plan: null,
  startDate: "",
  expiryDate: "",
};

export function PremiumProvider({
  children,
}: Props) {
  const [subscription, setSubscription] =
    useState<PremiumSubscription>(() => {
      const saved =
        localStorage.getItem("premium");

      if (saved) {
        return JSON.parse(saved);
      }

      return defaultSubscription;
    });

  useEffect(() => {
    if (!subscription.active) {
      return;
    }

    const expiry = new Date(
      subscription.expiryDate
    );

    if (expiry <= new Date()) {
      setSubscription(defaultSubscription);

      localStorage.removeItem("premium");
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      "premium",
      JSON.stringify(subscription)
    );
  }, [subscription]);

  const activatePremium = (
    plan: PremiumPlan
  ) => {
    const today = new Date();

    const expiry = new Date(today);

    expiry.setDate(
      expiry.getDate() + plan.duration
    );

    setSubscription({
      active: true,

      plan,

      startDate: today.toISOString(),

      expiryDate: expiry.toISOString(),
    });
  };

  const deactivatePremium = () => {
    setSubscription(defaultSubscription);

    localStorage.removeItem("premium");
  };

  const daysRemaining =
    subscription.active
      ? Math.max(
          0,
          Math.ceil(
            (new Date(
              subscription.expiryDate
            ).getTime() -
              Date.now()) /
              (1000 * 60 * 60 * 24)
          )
        )
      : 0;

  return (
    <PremiumContext.Provider
      value={{
        subscription,
        activatePremium,
        deactivatePremium,
        daysRemaining,
      }}
    >
      {children}
    </PremiumContext.Provider>
  );
}

export function usePremium() {
  const context =
    useContext(PremiumContext);

  if (!context) {
    throw new Error(
      "usePremium must be used inside PremiumProvider"
    );
  }

  return context;
}