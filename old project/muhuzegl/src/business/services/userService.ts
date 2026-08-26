import type { User, UserRole, UserStatus } from "../../types/user";

export class UserService {
  private storageKey = "users";

  /**
   * Get all users
   */
  getAll(): User[] {
    return JSON.parse(
      localStorage.getItem(this.storageKey) || "[]"
    );
  }

  /**
   * Save all users
   */
  private save(users: User[]): void {
    localStorage.setItem(
      this.storageKey,
      JSON.stringify(users)
    );
  }

  /**
   * Create User
   */
  create(user: User): void {
    const users = this.getAll();

    users.push(user);

    this.save(users);
  }

  /**
   * Find User By ID
   */
  findById(id: string): User | undefined {
    return this.getAll().find(
      (user) => user._id === id
    );
  }

  /**
   * Find User By Email
   */
 findByEmail(email: string): User | undefined {
  return this.getAll().find(
    (user) =>
      user.email.trim().toLowerCase() ===
      email.trim().toLowerCase()
  );
}
  /**
   * Find User By Phone
   */
  findByPhone(phone: string): User | undefined {
  return this.getAll().find((user) => {
    if (
      !user ||
      typeof user.phone !== "string"
    ) {
      return false;
    }

    return user.phone === phone;
  });
}

  /**
   * Find User By Referral Code
   */
  findByReferralCode(
    referralCode: string
  ): User | undefined {
    return this.getAll().find(
      (user) =>
        user.referralCode === referralCode
    );
  }

  /**
   * Update User
   */
  update(updatedUser: User): void {
    const users = this.getAll();

    const index = users.findIndex(
      (user) => user._id === updatedUser._id
    );

    if (index === -1) return;

    users[index] = updatedUser;

    this.save(users);
  }

  /**
   * Delete User
   */
  delete(id: string): void {
    const users = this.getAll().filter(
      (user) => user._id !== id
    );

    this.save(users);
  }

  /**
   * Become Seller
   */
  becomeSeller(id:string): void {
    const user = this.findById(id);

    if (!user) return;

    user.role = "seller";

    user.updatedAt = new Date().toISOString();

    this.update(user);
  }

  /**
   * Verify Seller
   */
  verifySeller(id: string): void {
    const user = this.findById(id);

    if (!user) return;

    user.sellerVerified = true;

    user.updatedAt = new Date().toISOString();

    this.update(user);
  }

  /**
   * Change Account Status
   */
  setStatus(
    id: string,
    status: UserStatus
  ): void {
    const user = this.findById(id);

    if (!user) return;

    user.status = status;

    user.updatedAt = new Date().toISOString();

    this.update(user);
  }

  /**
   * Change User Role
   */
  setRole(
    id: string,
    role: UserRole
  ): void {
    const user = this.findById(id);

    if (!user) return;

    user.role = role;

    user.updatedAt = new Date().toISOString();

    this.update(user);
  }

  /**
   * Email Exists
   */
  emailExists(email: string): boolean {
    return !!this.findByEmail(email);
  }

  /**
   * Phone Exists
   */
  phoneExists(phone: string): boolean {
    return !!this.findByPhone(phone);
  }

  /**
   * Referral Exists
   */
  referralExists(
    referralCode: string
  ): boolean {
    return !!this.findByReferralCode(
      referralCode
    );
  }
}