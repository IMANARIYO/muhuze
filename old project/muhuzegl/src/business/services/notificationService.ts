import type { Notification } from "../../types/notification";

export class NotificationService {
  private storageKey = "notifications";

  private getAll(): Notification[] {
    const data = localStorage.getItem(this.storageKey);

    return data ? JSON.parse(data) : [];
  }

  private save(notifications: Notification[]) {
    localStorage.setItem(
      this.storageKey,
      JSON.stringify(notifications)
    );
  }

  create(notification: Notification) {
    const notifications = this.getAll();

    notifications.unshift(notification);

    this.save(notifications);
  }

  getByUser(userId: string) {
    return this.getAll().filter(
      notification => notification.userId === userId
    );
  }

  markAsRead(id: string) {
    const notifications = this.getAll();

    const notification = notifications.find(
      item => item.id === id
    );

    if (notification) {
      notification.read = true;
    }

    this.save(notifications);
  }

  unreadCount(userId: string) {
    return this.getByUser(userId).filter(
      notification => !notification.read
    ).length;
  }
}