import { FaCheckCircle, FaTimesCircle } from "react-icons/fa";

import { useAuth } from "../../../context/AuthContext";

export default function VerificationStatus() {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  const emailVerified =
    currentUser.isEmailVerified === true;

  const phoneVerified =
    currentUser.isPhoneVerified === true;

  const sellerVerified =
    currentUser.sellerVerified === true;

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h3 className="text-2xl font-bold mb-2">
        Account Verification
      </h3>

      <p className="text-gray-500 mb-6">
        Your MUHUZE verification status.
      </p>

      <div className="space-y-4">

        {/* Email */}

        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">

          <div>
            <p className="font-semibold">
              Email Verification
            </p>

            <p className="text-sm text-gray-500">
              {currentUser.email}
            </p>
          </div>

          {emailVerified ? (
            <span className="flex items-center gap-2 text-green-600 font-medium">
              <FaCheckCircle />
              Verified
            </span>
          ) : (
            <span className="flex items-center gap-2 text-red-500 font-medium">
              <FaTimesCircle />
              Not Verified
            </span>
          )}

        </div>

        {/* Phone */}

        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">

          <div>
            <p className="font-semibold">
              Phone Verification
            </p>

            <p className="text-sm text-gray-500">
              {currentUser.phone || "No phone number"}
            </p>
          </div>

          {phoneVerified ? (
            <span className="flex items-center gap-2 text-green-600 font-medium">
              <FaCheckCircle />
              Verified
            </span>
          ) : (
            <span className="flex items-center gap-2 text-red-500 font-medium">
              <FaTimesCircle />
              Not Verified
            </span>
          )}

        </div>

        {/* Seller */}

        <div className="flex items-center justify-between p-4 rounded-xl bg-gray-50">

          <div>
            <p className="font-semibold">
              Seller Verification
            </p>

            <p className="text-sm text-gray-500">
              MUHUZE seller account status
            </p>
          </div>

          {sellerVerified ? (
            <span className="flex items-center gap-2 text-green-600 font-medium">
              <FaCheckCircle />
              Verified Seller
            </span>
          ) : (
            <span className="flex items-center gap-2 text-gray-500 font-medium">
              Not Verified
            </span>
          )}

        </div>

      </div>

    </div>
  );
}