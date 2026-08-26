import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import MainLayout from "../layouts/MainLayout";

// ==========================================
// PUBLIC PAGES
// ==========================================

import Home from "../pages/Home/Home";
import Login from "../pages/Login";
import Register from "../pages/Register";

import Marketplace from "../pages/Marketplace";
import MarketplaceCategory from "../pages/MarketplaceCategory";
import MarketplaceDetails from "../pages/MarketplaceDetails";

import Categories from "../pages/Categories/Categories";
import Premium from "../pages/Premium/Premium";

import ForgotPassword from "../pages/ForgotPassword";
import ResetPassword from "../pages/ResetPassword";

// ==========================================
// PROTECTED USER PAGES
// ==========================================

import Cart from "../pages/Cart";
import Checkout from "../pages/Checkout";
import OrderConfirmation from "../pages/OrderConfirmation";

import Profile from "../pages/Profile";
import Wallet from "../pages/Wallet/Wallet";

import Notifications from "../pages/Notifications";
import Wishlist from "../pages/Wishlist";

import MyOrders from "../pages/Orders";
import OrderDetails from "../pages/Orders/OrderDetails";

import Referral from "../pages/Referral/Referral";

// ==========================================
// SELLER PAGES
// ==========================================

import SellerDashboard, {
  MyListings,
} from "../pages/SellerDashboard";

import UploadProduct from "../pages/UploadMarketplaceItem/UploadMarketplaceItem";

import SellerOrders from "../pages/SellerDashboard/SellerOrders";

// ==========================================
// ADMIN PAGES
// ==========================================

import AdminWithdrawals from "../pages/Admin/AdminWithdrawals";
import WalletTransactions from "../pages/Admin/WalletTransactions";

// ==========================================
// AUTHENTICATION
// ==========================================

import ProtectedRoute from "../components/auth/ProtectedRoute";
import EditProfile from "../pages/Profile/EditProfile";
import VerifyEmail from "../pages/VerifyEmail/VerifyEmail";

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>

        {/* =====================================================
            MAIN APPLICATION LAYOUT
        ====================================================== */}

        <Route element={<MainLayout />}>

          {/* =================================================
              PUBLIC ROUTES
          ================================================== */}

          <Route
            path="/"
            element={<Home />}
          />

          <Route
            path="/login"
            element={<Login />}
          />

          <Route
            path="/register"
            element={<Register />}
          />

          {/* ===============================================
              MARKETPLACE
          ================================================ */}

          <Route
            path="/marketplace"
            element={<Marketplace />}
          />

          <Route
            path="/marketplace/category/:categoryId"
            element={<MarketplaceCategory />}
          />

          <Route
            path="/marketplace/:id"
            element={<MarketplaceDetails />}
          />

          {/* ===============================================
              OTHER PUBLIC PAGES
          ================================================ */}

          <Route
            path="/categories"
            element={<Categories />}
          />

          <Route
            path="/premium"
            element={<Premium />}
          />

          {/* ===============================================
              PASSWORD RECOVERY
          ================================================ */}

          <Route
            path="/forgot-password"
            element={<ForgotPassword />}
          />

          <Route
            path="/reset-password/:token"
            element={<ResetPassword />}
          />
          <Route
          path="/verify-email/:token"
          element={<VerifyEmail />}
          />

          {/* =================================================
              AUTHENTICATED USER ROUTES
          ================================================== */}

          {/* CART */}

          <Route
            path="/cart"
            element={
              <ProtectedRoute>
                <Cart />
              </ProtectedRoute>
            }
          />

          {/* CHECKOUT */}

          <Route
            path="/checkout"
            element={
              <ProtectedRoute>
                <Checkout />
              </ProtectedRoute>
            }
          />

          {/* ORDER CONFIRMATION */}

          <Route
            path="/order-confirmation"
            element={
              <ProtectedRoute>
                <OrderConfirmation />
              </ProtectedRoute>
            }
          />

          {/* PROFILE */}

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
  path="/profile/edit"
  element={
    <ProtectedRoute>
      <EditProfile />
    </ProtectedRoute>
  }
/>

          {/* WALLET */}

          <Route
            path="/wallet"
            element={
              <ProtectedRoute>
                <Wallet />
              </ProtectedRoute>
            }
          />

          {/* WISHLIST */}

          <Route
            path="/wishlist"
            element={
              <ProtectedRoute>
                <Wishlist />
              </ProtectedRoute>
            }
          />

          {/* NOTIFICATIONS */}

          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <Notifications />
              </ProtectedRoute>
            }
          />

          {/* ===============================================
              BUYER ORDERS
          ================================================ */}

          <Route
            path="/orders"
            element={
              <ProtectedRoute>
                <MyOrders />
              </ProtectedRoute>
            }
          />

          <Route
            path="/orders/:id"
            element={
              <ProtectedRoute>
                <OrderDetails />
              </ProtectedRoute>
            }
          />

          {/* ===============================================
              REFERRAL
          ================================================ */}

          <Route
            path="/referral"
            element={
              <ProtectedRoute>
                <Referral />
              </ProtectedRoute>
            }
          />

          {/* =================================================
              SELLER DASHBOARD
              SELLER + ADMIN
          ================================================== */}

          <Route
            path="/seller-dashboard"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "seller",
                  "admin",
                ]}
              >
                <SellerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
  path="/dashboard"
  element={
    <ProtectedRoute
      allowedRoles={[
        "seller",
        "admin",
      ]}
    >
      <SellerDashboard />
    </ProtectedRoute>
  }
/>

          {/* ===============================================
              SELLER PRODUCT MANAGEMENT
          ================================================ */}

          <Route
            path="/upload-product"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "seller",
                  "admin",
                ]}
              >
                <UploadProduct />
              </ProtectedRoute>
            }
          />

          <Route
            path="/upload-product/:id"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "seller",
                  "admin",
                ]}
              >
                <UploadProduct />
              </ProtectedRoute>
            }
          />

          {/* ===============================================
              SELLER LISTINGS
          ================================================ */}

          <Route
            path="/my-listings"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "seller",
                  "admin",
                ]}
              >
                <MyListings />
              </ProtectedRoute>
            }
          />

          {/* ===============================================
              SELLER ORDERS
          ================================================ */}

          <Route
            path="/seller-orders"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "seller",
                  "admin",
                ]}
              >
                <SellerOrders />
              </ProtectedRoute>
            }
          />

          {/* =================================================
              ADMIN ROUTES
              ADMIN ONLY
          ================================================== */}

          <Route
            path="/admin/withdrawals"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                ]}
              >
                <AdminWithdrawals />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/wallet-transactions"
            element={
              <ProtectedRoute
                allowedRoles={[
                  "admin",
                ]}
              >
                <WalletTransactions />
              </ProtectedRoute>
            }
          />

        </Route>

      </Routes>
    </BrowserRouter>
  );
}