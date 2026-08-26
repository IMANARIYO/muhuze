import { useAuth } from "../../../context/AuthContext";

export default function ProfileInfo() {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h3 className="text-2xl font-bold mb-6">
        Personal Information
      </h3>

      <div className="grid md:grid-cols-2 gap-6">

        {/* Full Name */}

        <div>
          <p className="text-sm text-gray-500">
            Full Name
          </p>

          <p className="font-medium">
            {currentUser.fullName}
          </p>
        </div>

        {/* Email */}

        <div>
          <p className="text-sm text-gray-500">
            Email
          </p>

          <p className="font-medium">
            {currentUser.email}
          </p>
        </div>

        {/* Phone */}

        <div>
          <p className="text-sm text-gray-500">
            Phone
          </p>

          <p className="font-medium">
            {currentUser.phone}
          </p>
        </div>

        {/* Role */}

        <div>
          <p className="text-sm text-gray-500">
            Role
          </p>

          <p className="font-medium capitalize">
            {currentUser.role}
          </p>
        </div>

        {/* Country */}

        <div>
          <p className="text-sm text-gray-500">
            Country
          </p>

          <p className="font-medium">
            {currentUser.country || "Not set"}
          </p>
        </div>

        {/* Province */}

        <div>
          <p className="text-sm text-gray-500">
            Province / City
          </p>

          <p className="font-medium">
            {currentUser.province || "Not set"}
          </p>
        </div>

        {/* District */}

        <div>
          <p className="text-sm text-gray-500">
            District
          </p>

          <p className="font-medium">
            {currentUser.district || "Not set"}
          </p>
        </div>

        {/* Sector */}

        <div>
          <p className="text-sm text-gray-500">
            Sector
          </p>

          <p className="font-medium">
            {currentUser.sector || "Not set"}
          </p>
        </div>

        {/* Cell */}

        <div>
          <p className="text-sm text-gray-500">
            Cell
          </p>

          <p className="font-medium">
            {currentUser.cell || "Not set"}
          </p>
        </div>

        {/* Village */}

        <div>
          <p className="text-sm text-gray-500">
            Village
          </p>

          <p className="font-medium">
            {currentUser.village || "Not set"}
          </p>
        </div>

        {/* Referral Code */}

        <div>
          <p className="text-sm text-gray-500">
            Referral Code
          </p>

          <p className="font-medium">
            {currentUser.referralCode ||
              "Not set"}
          </p>
        </div>

        {/* Member Since */}

        <div>
          <p className="text-sm text-gray-500">
            Member Since
          </p>

          <p className="font-medium">
            {new Date(
              currentUser.createdAt
            ).toLocaleDateString()}
          </p>
        </div>

      </div>

    </div>
  );
}