import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

export interface Notification {
  id: number;
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
}

interface NotificationContextType {
  notifications: Notification[];

  addNotification: (
    title: string,
    message: string
  ) => void;

  markAsRead: (id: number) => void;

  clearNotifications: () => void;
}

const NotificationContext =
  createContext<
    NotificationContextType | undefined
  >(undefined);

interface Props {
  children: ReactNode;
}

export function NotificationProvider({
  children,
}: Props) {
  const [notifications, setNotifications] =
    useState<Notification[]>([]);

  const addNotification = (
    title: string,
    message: string
  ) => {
    setNotifications((current) => [
      {
        id: Date.now(),
        title,
        message,
        read: false,
        createdAt: new Date().toISOString(),
      },
      ...current,
    ]);
  };

  const markAsRead = (id: number) => {
    setNotifications((current) =>
      current.map((notification) =>
        notification.id === id
          ? {
              ...notification,
              read: true,
            }
          : notification
      )
    );
  };

  const clearNotifications = () => {
    setNotifications([]);
  };

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        addNotification,
        markAsRead,
        clearNotifications,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(
    NotificationContext
  );

  if (!context) {
    throw new Error(
      "useNotifications must be used inside NotificationProvider"
    );
  }

  return context;
}

export default NotificationContext;