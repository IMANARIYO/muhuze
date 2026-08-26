export interface AuditLog {
  id: number;

  userId: string;

  action: string;

  entity: string;

  entityId: string;

  details: string;

  createdAt: string;
}