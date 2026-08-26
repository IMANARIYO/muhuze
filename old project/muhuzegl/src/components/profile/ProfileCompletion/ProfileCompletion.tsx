import { Link } from "react-router-dom";

import { useAuth } from "../../../context/AuthContext";

import { getProfileCompletion } from "../../../utils/profileCompletion";

export default function ProfileCompletion() {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  const {
    percentage,
    missing,
  } =
    getProfileCompletion(
      currentUser
    );

  const isComplete =
    percentage === 100;

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

        <div>
          <h3 className="text-2xl font-bold">
            Profile Completion
          </h3>

          <p className="text-gray-500 mt-1">
            Complete your profile to get
            the most from MUHUZE.
          </p>
        </div>

        <div className="text-3xl font-bold text-blue-600">
          {percentage}%
        </div>

      </div>

      {/* Progress Bar */}

      <div className="mt-6">

        <div className="w-full h-4 bg-gray-200 rounded-full overflow-hidden">

          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-500"
            style={{
              width: `${percentage}%`,
            }}
          />

        </div>

      </div>

      {/* Status */}

      {isComplete ? (

        <div className="mt-5 p-4 rounded-xl bg-green-50 border border-green-200 text-green-700">
          🎉 Your profile is complete!
        </div>

      ) : (

        <div className="mt-6">

          <p className="font-medium mb-3">
            Complete these items:
          </p>

          <div className="flex flex-wrap gap-2">

            {missing.map(
              (item) => (
                <span
                  key={item}
                  className="px-3 py-1 rounded-full bg-gray-100 text-gray-700 text-sm"
                >
                  {item}
                </span>
              )
            )}

          </div>

          <Link
            to="/profile/edit"
            className="inline-block mt-5 bg-blue-600 text-white px-5 py-3 rounded-xl hover:bg-blue-700 transition"
          >
            Complete Profile
          </Link>

        </div>

      )}

    </div>
  );
}