import express from "express";

import userController from "../controllers/userController.js";

import protect from "../middleware/authMiddleware.js";

import upload from "../middleware/upload.js";

const router = express.Router();


// ==========================================
// REGISTER TEST
// ==========================================

router.get(
  "/register",
  (req, res) => {
    res.send(
      "✅ Register route is working!"
    );
  }
);


// ==========================================
// REGISTER
// ==========================================

router.post(
  "/register",
  userController.registerUser
);

router.get(
  "/verify-email/:token",
  userController.verifyEmail
);

// ==========================================
// LOGIN
// ==========================================

router.post(
  "/login",
  userController.loginUser
);


// ==========================================
// CURRENT USER
// ==========================================

router.get(
  "/me",
  protect,
  userController.getCurrentUser
);


// ==========================================
// UPDATE PROFILE
// ==========================================

router.put(
  "/profile",
  protect,
  userController.updateProfile
);


// ==========================================
// UPDATE PROFILE IMAGE
// ==========================================

router.put(
  "/profile/image",
  protect,
  upload.single("profileImage"),
  userController.updateProfileImage
);


export default router;