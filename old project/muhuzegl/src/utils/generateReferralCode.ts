export function generateReferralCode(
  name: string
) {
  const prefix = name
    .trim()
    .split(" ")[0]
    .toUpperCase();

  const random = Math.floor(
    100000 + Math.random() * 900000
  );

  return `${prefix}-${random}`;
}