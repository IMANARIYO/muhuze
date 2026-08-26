import crypto from "crypto";

const sortObject = (obj) => {
  if (
    obj === null ||
    typeof obj !== "object"
  ) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(sortObject);
  }

  return Object.keys(obj)
    .sort()
    .reduce((result, key) => {
      result[key] = sortObject(obj[key]);

      return result;
    }, {});
};

const verifyNowPaymentsSignature = (
  payload,
  receivedSignature
) => {
  const secret =
    process.env.NOWPAYMENTS_IPN_SECRET;

  if (!secret) {
    throw new Error(
      "NOWPAYMENTS_IPN_SECRET is not configured"
    );
  }

  if (
    !receivedSignature ||
    typeof receivedSignature !== "string"
  ) {
    return false;
  }

  const sortedPayload =
    JSON.stringify(
      sortObject(payload)
    );

  const expectedSignature =
    crypto
      .createHmac(
        "sha512",
        secret
      )
      .update(sortedPayload)
      .digest("hex");

  const expectedBuffer =
    Buffer.from(
      expectedSignature,
      "utf8"
    );

  const receivedBuffer =
    Buffer.from(
      receivedSignature,
      "utf8"
    );

  // Prevent timingSafeEqual from
  // throwing when lengths differ.
  if (
    expectedBuffer.length !==
    receivedBuffer.length
  ) {
    return false;
  }

  return crypto.timingSafeEqual(
    expectedBuffer,
    receivedBuffer
  );
};

export default verifyNowPaymentsSignature;