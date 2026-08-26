import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  LoginData,
  RegisterData,
} from "../types/auth";

import type { User } from "../types/user";

import { authService } from "../business/services/authService";

interface AuthContextType {
  currentUser: User | null;

  isAuthenticated: boolean;

  loading: boolean;

  login: (
    data: LoginData
  ) => Promise<boolean>;

  register: (
    data: RegisterData
  ) => Promise<boolean>;

  logout: () => void;
updateProfile: (
  data: {
    fullName: string;
    phone?: string;
  }
) => Promise<boolean>;
}

const AuthContext =
  createContext<AuthContextType | null>(null);

interface Props {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: Props) {
  const [
    currentUser,
    setCurrentUser,
  ] = useState<User | null>(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  /**
   * ==========================================
   * CHECK AUTHENTICATION ON APP START
   * ==========================================
   */

  useEffect(() => {
    async function restoreAuthentication() {
      try {
        const token =
          authService.getToken();

        // No token means user is not authenticated.
        if (!token) {
          setCurrentUser(null);
          return;
        }

        // Verify token with the real backend.
        const user =
          await authService.getAuthenticatedUser();

        setCurrentUser(user);
      } catch (error) {
        console.error(
          "AUTH RESTORE ERROR:",
          error
        );

        // Token is invalid or expired.
        authService.logout();

        setCurrentUser(null);
      } finally {
        setLoading(false);
      }
    }

    restoreAuthentication();
  }, []);

  /**
   * ==========================================
   * LOGIN
   * ==========================================
   */

  async function login(
    data: LoginData
  ): Promise<boolean> {
    try {
      const user =
        await authService.login(data);

      setCurrentUser(user);

      return true;
    } catch (error) {
      console.error(
        "LOGIN ERROR:",
        error
      );

      if (error instanceof Error) {
        alert(error.message);
      }

      return false;
    }
  }

  /**
   * ==========================================
   * REGISTER
   * ==========================================
   */

  async function register(
    data: RegisterData
  ): Promise<boolean> {
    try {
      const user =
        await authService.register(data);

      setCurrentUser(user);

      return true;
    } catch (error) {
      console.error(
        "REGISTER ERROR:",
        error
      );

      if (error instanceof Error) {
        alert(error.message);
      }

      return false;
    }
  }

  /**
   * ==========================================
   * UPDATE PROFILE
   * ==========================================
   */

  async function updateProfile(
  data: {
    fullName: string;
    phone?: string;
  }
): Promise<boolean> {
  try {
    const updatedUser =
      await authService.updateProfile(
        data
      );

    setCurrentUser(
      updatedUser
    );

    return true;
  } catch (error) {
    console.error(
      "UPDATE PROFILE ERROR:",
      error
    );

    if (error instanceof Error) {
      alert(error.message);
    }

    return false;
  }
}

  /**
   * ==========================================
   * LOGOUT
   * ==========================================
   */

  function logout() {
    authService.logout();

    setCurrentUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        currentUser,

        isAuthenticated:
          currentUser !== null,

        loading,

        login,

        register,

        logout,

        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * ==========================================
 * USE AUTH
 * ==========================================
 */

export function useAuth() {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider."
    );
  }

  return context;
}