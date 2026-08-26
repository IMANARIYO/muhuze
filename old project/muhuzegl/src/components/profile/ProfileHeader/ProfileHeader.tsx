import {
  useRef,
  useState,
  type ChangeEvent,
} from "react";

import {
  FaUserCircle,
  FaCheckCircle,
} from "react-icons/fa";

import { useAuth } from "../../../context/AuthContext";

interface UpdateProfileImageResponse {
  success: boolean;
  message: string;
  user: any;
}

export default function ProfileHeader() {
  const {
    currentUser,
    updateProfile,
  } = useAuth();

  const fileInputRef =
    useRef<HTMLInputElement | null>(null);

  const [uploading, setUploading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  if (!currentUser) {
    return null;
  }

  // ==========================================
  // OPEN FILE SELECTOR
  // ==========================================

  function handleChooseImage() {
    setError("");
    setSuccess("");

    fileInputRef.current?.click();
  }

  // ==========================================
  // IMAGE SELECTED
  // ==========================================

  async function handleImageChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");
    setSuccess("");

    // ========================================
    // CHECK FILE TYPE
    // ========================================

    if (!file.type.startsWith("image/")) {
      setError(
        "Please select an image file."
      );

      event.target.value = "";

      return;
    }

    // ========================================
    // CHECK FILE SIZE
    // ========================================

    const maxSize =
      5 * 1024 * 1024;

    if (file.size > maxSize) {
      setError(
        "Image must be smaller than 5 MB."
      );

      event.target.value = "";

      return;
    }

    try {
      setUploading(true);

      // ======================================
      // CREATE FORM DATA
      // ======================================

      const formData =
        new FormData();

      formData.append(
        "profileImage",
        file
      );

      // ======================================
      // UPLOAD IMAGE
      // ======================================

      const token =
        localStorage.getItem(
          "authToken"
        );

      const response =
        await fetch(
          "http://localhost:5000/api/users/profile/image",
          {
            method: "PUT",

            headers: token
              ? {
                  Authorization:
                    `Bearer ${token}`,
                }
              : undefined,

            body: formData,
          }
        );

      const result =
        (await response.json()) as
          UpdateProfileImageResponse;

      if (!response.ok) {
        throw new Error(
          result.message ||
            "Profile image upload failed."
        );
      }

      if (
        !result.success ||
        !result.user
      ) {
        throw new Error(
          result.message ||
            "Profile image upload failed."
        );
      }

      // ======================================
      // UPDATE AUTH STATE
      // ======================================

      updateProfile(
        result.user
      );

      setSuccess(
        "Profile picture updated successfully."
      );

    } catch (error) {
      console.error(
        "PROFILE IMAGE UPLOAD ERROR:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to upload profile picture."
      );
    } finally {
      setUploading(false);

      // Allow selecting the same
      // image again later.
      event.target.value = "";
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-8 flex flex-col md:flex-row items-center gap-6">

      {/* ======================================
          PROFILE PICTURE
      ======================================= */}

      <div className="flex flex-col items-center gap-3">

        {currentUser.profileImage ? (
          <img
  src={`http://localhost:5000${currentUser.profileImage}`}
  alt={currentUser.fullName}
            className="w-28 h-28 rounded-full object-cover border-4 border-blue-600"
          />
        ) : (
          <FaUserCircle className="text-8xl text-gray-400" />
        )}

        {/* Hidden file input */}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={
            handleImageChange
          }
          className="hidden"
        />

        {/* Change picture button */}

        <button
          type="button"
          onClick={
            handleChooseImage
          }
          disabled={uploading}
          className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {uploading
            ? "Uploading..."
            : "Change Picture"}
        </button>

      </div>

      {/* ======================================
          USER INFORMATION
      ======================================= */}

      <div className="flex-1">

        <h2 className="text-3xl font-bold">
          {currentUser.fullName}
        </h2>

        <div className="mt-2 space-y-1 text-gray-600">

          <p>
            <strong>Email:</strong>{" "}
            {currentUser.email}
          </p>

          <p>
            <strong>Phone:</strong>{" "}
            {currentUser.phone}
          </p>

        </div>

        {/* ====================================
            BADGES
        ===================================== */}

        <div className="flex flex-wrap gap-3 mt-4">

          <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm">
            {currentUser.role.toUpperCase()}
          </span>

          {currentUser.sellerVerified && (
            <span className="flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm">
              <FaCheckCircle />
              Verified Seller
            </span>
          )}

          {currentUser.premium?.active && (
            <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 text-sm">
              ⭐ Premium Member
            </span>
          )}

        </div>

        {/* ====================================
            MESSAGES
        ===================================== */}

        {error && (
          <div className="mt-4 rounded-xl bg-red-50 border border-red-200 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="mt-4 rounded-xl bg-green-50 border border-green-200 p-3 text-sm text-green-700">
            {success}
          </div>
        )}

      </div>

    </div>
  );
}