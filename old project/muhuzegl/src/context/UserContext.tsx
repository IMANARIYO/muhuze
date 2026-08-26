import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { User } from "../types/user";

interface UserContextType {
  currentUser: User | null;

  setCurrentUser: (
    user: User | null
  ) => void;

  logout: () => void;
}

const UserContext =
  createContext<UserContextType | null>(
    null
  );

export function UserProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [currentUser, setCurrentUser] =
    useState<User | null>(() => {
      const saved =
        localStorage.getItem("currentUser");

      return saved
        ? JSON.parse(saved)
        : null;
    });

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem(
        "currentUser",
        JSON.stringify(currentUser)
      );
    } else {
      localStorage.removeItem(
        "currentUser"
      );
    }
  }, [currentUser]);

  function logout() {
    setCurrentUser(null);
  }

  return (
    <UserContext.Provider
      value={{
        currentUser,
        setCurrentUser,
        logout,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context =
    useContext(UserContext);

  if (!context) {
    throw new Error(
      "useUser must be used inside UserProvider."
    );
  }

  return context;
}