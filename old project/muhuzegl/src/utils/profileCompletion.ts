import type { User } from "../types/user";

export interface ProfileCompletion {
  percentage: number;
  completed: number;
  total: number;
  missing: string[];
}

export function getProfileCompletion(
  user: User
): ProfileCompletion {
  const fields = [
    {
      label: "Full Name",
      completed:
        Boolean(user.fullName?.trim()),
      weight: 10,
    },

    {
      label: "Email",
      completed:
        Boolean(user.email?.trim()),
      weight: 10,
    },

    {
      label: "Phone",
      completed:
        Boolean(user.phone?.trim()),
      weight: 10,
    },

    {
      label: "Profile Picture",
      completed:
        Boolean(user.profileImage),
      weight: 10,
    },

    {
      label: "Bio",
      completed:
        Boolean(user.bio?.trim()),
      weight: 5,
    },

    {
      label: "Country",
      completed:
        Boolean(user.country?.trim()),
      weight: 5,
    },

    {
      label: "Province / City",
      completed:
        Boolean(user.province?.trim()),
      weight: 10,
    },

    {
      label: "District",
      completed:
        Boolean(user.district?.trim()),
      weight: 10,
    },

    {
      label: "Sector",
      completed:
        Boolean(user.sector?.trim()),
      weight: 10,
    },

    {
      label: "Cell",
      completed:
        Boolean(user.cell?.trim()),
      weight: 5,
    },

    {
      label: "Village",
      completed:
        Boolean(user.village?.trim()),
      weight: 5,
    },

    {
      label: "Email Verification",
      completed:
        Boolean(user.isEmailVerified),
      weight: 5,
    },

    {
      label: "Phone Verification",
      completed:
        Boolean(user.isPhoneVerified),
      weight: 5,
    },
  ];

  const total =
    fields.reduce(
      (sum, field) =>
        sum + field.weight,
      0
    );

  const completed =
    fields.reduce(
      (sum, field) =>
        sum +
        (field.completed
          ? field.weight
          : 0),
      0
    );

  const missing =
    fields
      .filter(
        (field) =>
          !field.completed
      )
      .map(
        (field) =>
          field.label
      );

  const percentage =
    Math.round(
      (completed / total) * 100
    );

  return {
    percentage,
    completed,
    total,
    missing,
  };
}