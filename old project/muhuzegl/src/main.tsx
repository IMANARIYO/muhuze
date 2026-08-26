import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";

import App from "./App";

import { AuthProvider } from "./context/AuthContext";
import { MarketplaceProvider } from "./context/MarketplaceContext";
import { UserProvider } from "./context/UserContext";
import { OrderProvider } from "./context/OrderContext";
import { CartProvider } from "./context/CartContext";
import { WishlistProvider } from "./context/WishlistContext";
import { NotificationProvider } from "./context/NotificationContext";
import { ReviewProvider } from "./context/ReviewContext";
import { WalletProvider } from "./context/WalletContext";
import { PremiumProvider } from "./context/PremiumContext";
import { ReferralProvider } from "./context/ReferralContext";
import { ReferralCommissionProvider } from "./context/ReferralCommissionContext";

import { ToastProvider } from "./components/ui/Toast";

createRoot(
  document.getElementById("root")!
).render(
  <StrictMode>
    <AuthProvider>
      <MarketplaceProvider>
        <UserProvider>
          <OrderProvider>
            <CartProvider>
              <WishlistProvider>
                <NotificationProvider>
                  <ReviewProvider>
                    <WalletProvider>
                      <ToastProvider>
                        <PremiumProvider>
                          <ReferralProvider>
                            <ReferralCommissionProvider>
                              <App />
                            </ReferralCommissionProvider>
                          </ReferralProvider>
                        </PremiumProvider>
                      </ToastProvider>
                    </WalletProvider>
                  </ReviewProvider>
                </NotificationProvider>
              </WishlistProvider>
            </CartProvider>
          </OrderProvider>
        </UserProvider>
      </MarketplaceProvider>
    </AuthProvider>
  </StrictMode>
);