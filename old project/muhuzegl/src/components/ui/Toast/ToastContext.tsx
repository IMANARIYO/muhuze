import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

import type {
  Toast,
  ToastType,
} from "./types";

import ToastContainer from "./ToastContainer";

interface ToastContextType {
  showToast: (
    message: string,
    type?: ToastType
  ) => void;
}

const ToastContext = createContext<
  ToastContextType | undefined
>(undefined);

interface Props {
  children: ReactNode;
}

export function ToastProvider({
  children,
}: Props) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (
    message: string,
    type: ToastType = "info"
  ) => {
    const id = Date.now();

    setToasts((current) => [
      ...current,
      {
        id,
        message,
        type,
      },
    ]);

    setTimeout(() => {
      setToasts((current) =>
        current.filter(
          (toast) => toast.id !== id
        )
      );
    }, 3000);
  };

  return (
    <ToastContext.Provider
      value={{ showToast }}
    >
      {children}

      <ToastContainer
        toasts={toasts}
      />

    </ToastContext.Provider>
  );
}

export function useToast() {
  const context =
    useContext(ToastContext);

  if (!context) {
    throw new Error(
      "useToast must be used inside ToastProvider"
    );
  }

  return context;
}