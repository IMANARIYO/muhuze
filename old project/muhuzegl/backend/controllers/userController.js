import bcrypt from "bcrypt";
import mongoose from "mongoose";
import jwt from "jsonwebtoken";
import crypto from "crypto";

import User from "../models/User.js";
import Referral from "../models/Referral.js";
import PasswordResetToken from "../models/PasswordResetToken.js";
import emailService from "../services/emailService.js";
/**
 * ==========================================
 * REGISTER USER
 * ==========================================
 */

const registerUser = async (
  req,
  res
) => {
  try {
    const {
      fullName,
      email,
      password,
      phone,
      referralCode,
    } = req.body;

    // =========================
    // BASIC VALIDATION
    // =========================

    if (!fullName) {
      return res.status(400).json({
        success: false,
        message:
          "Full name is required",
      });
    }

    if (!email) {
      return res.status(400).json({
        success: false,
        message:
          "Email is required",
      });
    }

    if (!password) {
      return res.status(400).json({
        success: false,
        message:
          "Password is required",
      });
    }

    // =========================
    // CHECK EXISTING USER
    // =========================

    const existingUser =
      await User.findOne({
        email,
      });

    if (existingUser) {
      return res.status(400).json({
        success: false,
        message:
          "Email already exists",
      });
    }

    // =========================
    // VALIDATE REFERRER
    // =========================

    let referrer = null;

    if (referralCode) {
      if (
        !mongoose.Types.ObjectId.isValid(
          referralCode
        )
      ) {
        return res.status(400).json({
          success: false,
          message:
            "Invalid referral link",
        });
      }

      referrer =
        await User.findById(
          referralCode
        );

      if (!referrer) {
        return res.status(400).json({
          success: false,
          message:
            "Referral user not found",
        });
      }
    }

    // =========================
    // HASH PASSWORD
    // =========================

    const hashedPassword =
      await bcrypt.hash(
        password,
        10
      );

    // =========================
    // CREATE USER
    // =========================

    const user =
      await User.create({
        fullName,
        email,
        password:
          hashedPassword,
        phone,
      });

    // =========================
    // CREATE REFERRAL
    // =========================

    if (referrer) {
      try {
        await Referral.create({
          referrer:
            referrer._id,

          referredUser:
            user._id,

          referralCode:
            referralCode,

          status: "Pending",
        });
      } catch (referralError) {
        await User.findByIdAndDelete(
          user._id
        );

        throw referralError;
      }
    }

    // =========================
    // REMOVE PASSWORD
    // =========================

    const {
      password: _,
      ...userWithoutPassword
    } = user.toObject();

    // =========================
    // RESPONSE
    // =========================

    res.status(201).json({
      success: true,

      message: referrer
        ? "User registered successfully through referral"
        : "User registered successfully",

      data:
        userWithoutPassword,
    });
  } catch (error) {
    console.error(
      "REGISTER ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message:
        error.message,
    });
  }
};

/**
 * ==========================================
 * LOGIN USER
 * ==========================================
 */

const loginUser = async (
  req,
  res
) => {
  try {
    const {
      email,
      password,
    } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message:
          "Email and password are required",
      });
    }

    // =========================
    // FIND USER
    // =========================

    const user =
      await User.findOne({
        email,
      });

    if (!user) {
      return res.status(400).json({
        success: false,
        message:
          "User not found",
      });
    }

    // =========================
    // CHECK PASSWORD
    // =========================

    const isMatch =
      await bcrypt.compare(
        password,
        user.password
      );

    if (!isMatch) {
      return res.status(400).json({
        success: false,
        message:
          "Incorrect password",
      });
    }

    // =========================
    // CREATE JWT
    // =========================

    const token =
      jwt.sign(
        {
          userId:
            user._id.toString(),
        },

        process.env.JWT_SECRET,

        {
          expiresIn: "7d",
        }
      );

    // =========================
    // REMOVE PASSWORD
    // =========================

    const {
      password: _,
      ...userWithoutPassword
    } = user.toObject();

    // =========================
    // RESPONSE
    // =========================

    res.status(200).json({
      success: true,

      message:
        "Login successful",

      token,

      user:
        userWithoutPassword,
    });
  } catch (error) {
    console.error(
      "LOGIN ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message:
        error.message,
    });
  }
};

/**
 * ==========================================
 * FORGOT PASSWORD
 * ==========================================
 *
 * POST
 * /api/users/forgot-password
 */

const forgotPassword = async (
  req,
  res
) => {
  try {
    const email =
      req.body.email
        ?.trim()
        .toLowerCase();

    if (!email) {
      return res.status(400).json({
        success: false,
        message:
          "Email is required.",
      });
    }

    // =========================
    // FIND USER
    // =========================

    const user =
      await User.findOne({
        email,
      });

    /**
     * Security:
     *
     * We don't reveal whether
     * an email exists.
     */

    if (!user) {
      return res.status(200).json({
        success: true,
        message:
          "If an account exists with this email, a password reset link will be sent.",
      });
    }

    // =========================
    // DELETE OLD TOKENS
    // =========================

    await PasswordResetToken.deleteMany({
      userId: user._id,
    });

    // =========================
    // CREATE RANDOM TOKEN
    // =========================

    const resetToken =
      crypto.randomBytes(32).toString(
        "hex"
      );

    // =========================
    // HASH TOKEN
    // =========================

    const tokenHash =
      crypto
        .createHash("sha256")
        .update(resetToken)
        .digest("hex");

    // =========================
    // EXPIRATION
    // =========================
    //
    // 30 minutes

    const expiresAt =
      new Date(
        Date.now() +
          30 * 60 * 1000
      );

    // =========================
    // SAVE TOKEN
    // =========================

    await PasswordResetToken.create({
      userId: user._id,

      tokenHash,

      expiresAt,

      used: false,
    });

    /**
     * ==========================================
     * TEMPORARY DEVELOPMENT RESET URL
     * ==========================================
     *
     * We will replace this with an actual
     * email service after the reset flow works.
     */

    const frontendUrl =
      process.env.FRONTEND_URL ||
      "http://localhost:5173";

    const resetUrl =
      `${frontendUrl}/reset-password/${resetToken}`;

    await emailService.sendPasswordResetEmail({
  email: user.email,
  resetUrl,
});

res.status(200).json({
  success: true,

  message:
    "If an account exists with this email, a password reset link will be sent.",
});
  } catch (error) {
    console.error(
      "FORGOT PASSWORD ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message:
        "Unable to process password reset request.",
    });
  }
};

/**
 * ==========================================
 * RESET PASSWORD
 * ==========================================
 *
 * POST
 * /api/users/reset-password/:token
 */

const resetPassword = async (
  req,
  res
) => {
  try {
    const { token } =
      req.params;

    const {
      password,
    } = req.body;

    // =========================
    // VALIDATION
    // =========================

    if (!token) {
      return res.status(400).json({
        success: false,
        message:
          "Reset token is required.",
      });
    }

    if (!password) {
      return res.status(400).json({
        success: false,
        message:
          "New password is required.",
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        message:
          "Password must be at least 6 characters.",
      });
    }

    // =========================
    // HASH TOKEN
    // =========================

    const tokenHash =
      crypto
        .createHash("sha256")
        .update(token)
        .digest("hex");

    // =========================
    // FIND RESET TOKEN
    // =========================

    const resetRecord =
      await PasswordResetToken.findOne({
        tokenHash,

        used: false,

        expiresAt: {
          $gt: new Date(),
        },
      });

    if (!resetRecord) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid or expired reset token.",
      });
    }

    // =========================
    // FIND USER
    // =========================

    const user =
      await User.findById(
        resetRecord.userId
      );

    if (!user) {
      return res.status(404).json({
        success: false,
        message:
          "User not found.",
      });
    }

    // =========================
    // HASH NEW PASSWORD
    // =========================

    const hashedPassword =
      await bcrypt.hash(
        password,
        10
      );

    // =========================
    // UPDATE PASSWORD
    // =========================

    user.password =
      hashedPassword;

    await user.save();

    // =========================
    // MARK TOKEN USED
    // =========================

    resetRecord.used =
      true;

    await resetRecord.save();

    // =========================
    // DELETE ANY OTHER TOKENS
    // =========================

    await PasswordResetToken.deleteMany(
      {
        userId: user._id,

        _id: {
          $ne: resetRecord._id,
        },
      }
    );

    // =========================
    // RESPONSE
    // =========================

    res.status(200).json({
      success: true,

      message:
        "Password reset successfully. You can now log in with your new password.",
    });
  } catch (error) {
    console.error(
      "RESET PASSWORD ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message:
        "Unable to reset password.",
    });
  }
};
/**
 * ==========================================
 * GET CURRENT AUTHENTICATED USER
 * ==========================================
 */

const getCurrentUser = async (req, res) => {
  try {
    return res.status(200).json({
      success: true,
      user: req.user,
    });
  } catch (error) {
    console.error(
      "GET CURRENT USER ERROR:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        "Unable to get current user.",
    });
  }
};
/**
 * ==========================================
 * UPDATE CURRENT USER PROFILE
 * ==========================================
 *
 * PUT
 * /api/users/profile
 */

const updateProfile = async (req, res) => {
  try {
    const {
      fullName,
      phone,
      bio,

      country,

      province,
      provinceId,

      district,
      districtId,

      sector,
      sectorId,

      cell,
      cellId,

      village,
      villageId,
    } = req.body;

    // ==========================================
    // BASIC VALIDATION
    // ==========================================

    if (!fullName || !fullName.trim()) {
      return res.status(400).json({
        success: false,
        message: "Full name is required.",
      });
    }

    // ==========================================
    // FIND CURRENT USER
    // ==========================================

    const user = await User.findById(
      req.user._id
    );

    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found.",
      });
    }

    // ==========================================
    // BASIC PROFILE INFORMATION
    // ==========================================

    user.fullName =
      fullName.trim();

    if (phone !== undefined) {
      user.phone =
        phone.trim();
    }

    if (bio !== undefined) {
      user.bio =
        bio.trim();
    }

    // ==========================================
    // RWANDA LOCATION
    // ==========================================

    if (country !== undefined) {
      user.country =
        country.trim();
    }

    if (province !== undefined) {
      user.province =
        province.trim();
    }

    if (provinceId !== undefined) {
      user.provinceId =
        provinceId.trim();
    }

    if (district !== undefined) {
      user.district =
        district.trim();
    }

    if (districtId !== undefined) {
      user.districtId =
        districtId.trim();
    }

    if (sector !== undefined) {
      user.sector =
        sector.trim();
    }

    if (sectorId !== undefined) {
      user.sectorId =
        sectorId.trim();
    }

    if (cell !== undefined) {
      user.cell =
        cell.trim();
    }

    if (cellId !== undefined) {
      user.cellId =
        cellId.trim();
    }

    if (village !== undefined) {
      user.village =
        village.trim();
    }

    if (villageId !== undefined) {
      user.villageId =
        villageId.trim();
    }

    // ==========================================
    // SAVE USER
    // ==========================================

    await user.save();

    // ==========================================
    // REMOVE PASSWORD FROM RESPONSE
    // ==========================================

    const {
      password: _,
      ...userWithoutPassword
    } = user.toObject();

    // ==========================================
    // RESPONSE
    // ==========================================

    return res.status(200).json({
      success: true,

      message:
        "Profile updated successfully.",

      user:
        userWithoutPassword,
    });

  } catch (error) {
    console.error(
      "UPDATE PROFILE ERROR:",
      error
    );

    return res.status(500).json({
      success: false,

      message:
        "Unable to update profile.",
    });
  }
};
const updateProfileImage = async (
  req,
  res
) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "Please select an image.",
      });
    }

    const user = await User.findById(
      req.user._id
    );

    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found.",
      });
    }

    user.profileImage =
      `/uploads/${req.file.filename}`;

    await user.save();

    const {
      password: _,
      ...userWithoutPassword
    } = user.toObject();

    return res.status(200).json({
      success: true,
      message:
        "Profile image updated successfully.",
      user: userWithoutPassword,
    });

  } catch (error) {
    console.error(
      "UPDATE PROFILE IMAGE ERROR:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        "Unable to update profile image.",
    });
  }
};
const verifyEmail = async (
  req,
  res
) => {
  try {
    const { token } = req.params;

    if (!token) {
      return res.status(400).json({
        success: false,
        message:
          "Verification token is required.",
      });
    }

    const user =
      await User.findOne({
        emailVerificationToken: token,
        emailVerificationExpires: {
          $gt: new Date(),
        },
      });

    if (!user) {
      return res.status(400).json({
        success: false,
        message:
          "Verification link is invalid or has expired.",
      });
    }

    user.isEmailVerified = true;

    // Keep legacy field synchronized
    user.isVerified = true;

    user.emailVerificationToken = "";

    user.emailVerificationExpires = null;

    await user.save();

    return res.status(200).json({
      success: true,
      message:
        "Email verified successfully.",
    });

  } catch (error) {
    console.error(
      "VERIFY EMAIL ERROR:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        "Unable to verify email.",
    });
  }
};


/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  registerUser,
  loginUser,
  forgotPassword,
  resetPassword,
  getCurrentUser,
  updateProfile,
  updateProfileImage,
  verifyEmail,
};