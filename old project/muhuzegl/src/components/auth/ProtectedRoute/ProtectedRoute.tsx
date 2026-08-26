import {
  Navigate,
  useLocation,
} from "react-router-dom";

import type { ReactNode } from "react";

import { useAuth } from "../../../context/AuthContext";

import type { UserRole } from "../../../types/user";

interface Props {
  children: ReactNode;

  allowedRoles?: UserRole[];
}

export default function ProtectedRoute({
  children,
  allowedRoles,
}: Props) {
  const {
    isAuthenticated,
    currentUser,
    loading,
  } = useAuth();

  const location =
    useLocation();

  /**
   * ==========================================
   * AUTHENTICATION CHECK
   * ==========================================
   */

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">

          <div
            className="
              h-10
              w-10
              animate-spin
              rounded-full
              border-4
              border-gray-200
              border-t-blue-600
              mx-auto
            "
          />

          <p className="mt-4 text-gray-500">
            Checking authentication...
          </p>

        </div>
      </div>
    );
  }

  /**
   * ==========================================
   * NOT LOGGED IN
   * ==========================================
   */

  if (!isAuthenticated || !currentUser) {
    return (
      <Navigate
        to="/login"
        state={{
          from: location,
        }}
        replace
      />
    );
  }

  /**
   * ==========================================
   * ROLE CHECK
   * ==========================================
   */

  if (
    allowedRoles &&
    !allowedRoles.includes(
      currentUser.role
    )
  ) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  /**
   * ==========================================
   * ACCESS GRANTED
   * ==========================================
   */

  return <>{children}</>;
}