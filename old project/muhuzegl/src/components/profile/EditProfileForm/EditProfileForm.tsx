import {
  useCallback,
  useState,
} from "react";
import { useAuth } from "../../../context/AuthContext";

import Input from "../../ui/Input";
import Button from "../../ui/Button";

import RwandaLocationSelector from "../../location/RwandaLocationSelector";

import { apiClient } from "../../../business/services/apiClient";

interface LocationData {
  provinceId: string;
  provinceName: string;

  districtId: string;
  districtName: string;

  sectorId: string;
  sectorName: string;

  cellId: string;
  cellName: string;

  villageId: string;
  villageName: string;
}

interface UpdateProfileResponse {
  success: boolean;
  message: string;
  user: any;
}

export default function EditProfileForm() {
  const {
    currentUser,
    updateProfile,
  } = useAuth();

  const [fullName, setFullName] =
    useState(
      currentUser?.fullName ?? ""
    );

  const [email, setEmail] =
    useState(
      currentUser?.email ?? ""
    );

  const [phone, setPhone] =
    useState(
      currentUser?.phone ?? ""
    );

  const [bio, setBio] =
    useState(
      currentUser?.bio ?? ""
    );

  const [location, setLocation] =
    useState<LocationData | null>(
      null
    );

  const [saving, setSaving] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  if (!currentUser) {
    return null;
  }

  const handleLocationChange =
  useCallback(
    (newLocation: LocationData) => {
      setLocation(newLocation);

      setError("");
      setMessage("");
    },
    []
  );

  async function handleSave() {
    setMessage("");
    setError("");

    if (!fullName.trim()) {
      setError(
        "Full name is required."
      );

      return;
    }

    if (!location) {
      setError(
        "Please select your complete Rwanda location."
      );

      return;
    }

    try {
      setSaving(true);

      const profileData = {
        fullName:
          fullName.trim(),

        phone:
          phone.trim(),

        bio:
          bio.trim(),

        email:
          email.trim(),

        country: "Rwanda",

        province:
          location.provinceName,

        provinceId:
          location.provinceId,

        district:
          location.districtName,

        districtId:
          location.districtId,

        sector:
          location.sectorName,

        sectorId:
          location.sectorId,

        cell:
          location.cellName,

        cellId:
          location.cellId,

        village:
          location.villageName,

        villageId:
          location.villageId,
      };

      const result =
        await apiClient.put<UpdateProfileResponse>(
          "/users/profile",
          profileData
        );

      if (
        !result.success ||
        !result.user
      ) {
        throw new Error(
          result.message ||
            "Profile update failed."
        );
      }

      /*
       * Update React authentication state
       * with the user returned by MongoDB.
       */
      updateProfile(
        result.user
      );

      setMessage(
        "Profile updated successfully."
      );

      console.log(
        "PROFILE UPDATED:",
        result.user
      );

    } catch (error) {
      console.error(
        "PROFILE UPDATE ERROR:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to update profile."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-8">

      {/* =====================================
          PERSONAL INFORMATION
      ====================================== */}

      <div className="bg-white rounded-2xl shadow-md p-8">

        <h3 className="text-2xl font-bold mb-6">
          Personal Information
        </h3>

        <div className="space-y-5">

          <Input
            label="Full Name"
            value={fullName}
            onChange={(event) =>
              setFullName(
                event.target.value
              )
            }
          />

          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
          />

          <Input
            label="Phone"
            value={phone}
            onChange={(event) =>
              setPhone(
                event.target.value
              )
            }
          />

          <Input
            label="Bio"
            value={bio}
            onChange={(event) =>
              setBio(
                event.target.value
              )
            }
          />

        </div>

      </div>

      {/* =====================================
          RWANDA LOCATION
      ====================================== */}

      <div className="bg-white rounded-2xl shadow-md p-8">

        <h3 className="text-2xl font-bold mb-2">
          Location
        </h3>

        <p className="text-gray-500 mb-6">
          Select your official Rwanda
          administrative location.
        </p>

        <RwandaLocationSelector
          onChange={
            handleLocationChange
          }
        />

      </div>

      {/* =====================================
          STATUS MESSAGES
      ====================================== */}

      {error && (
        <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-700">
          {error}
        </div>
      )}

      {message && (
        <div className="rounded-xl bg-green-50 border border-green-200 p-4 text-green-700">
          {message}
        </div>
      )}

      {/* =====================================
          SAVE
      ====================================== */}

      <div className="flex justify-end">

        <Button
          onClick={handleSave}
          disabled={saving}
        >
          {saving
            ? "Saving..."
            : "Save Changes"}
        </Button>

      </div>

    </div>
  );
}