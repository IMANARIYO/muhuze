import type {
  Notification,
  NotificationType,
} from "../../types/notification";

export class NotificationEngine {

  private notifications: Notification[];

constructor(
  notifications: Notification[]
) {
  this.notifications = notifications;
}
  create(
    userId:string,

    title:string,

    message:string,

    type:NotificationType
  ){

      this.notifications.unshift({

          id: crypto.randomUUID(),

          userId,

          title,

          message,

          type,

          read:false,

          createdAt:new Date().toISOString(),

      });

  }

}