import {
  useState,
} from "react";

import {
  useSearchParams,
} from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";
import { useAuth } from "../../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [
    fullName,
    setFullName,
  ] = useState("");

  const [
    email,
    setEmail,
  ] = useState("");

  const [
    phoneNumber,
    setPhoneNumber,
  ] = useState("");

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");

  const [
    chooseSex,
    setChooseSex,
  ] = useState("");

  const [
    acceptTerms,
    setAcceptTerms,
  ] = useState(false);

  const [
    registerDate,
    setRegisterDate,
  ] = useState(new Date());

  const { showToast } =
    useToast();

  const navigate =
    useNavigate();

  const { register } =
    useAuth();

  /**
   * ==========================================
   * READ REFERRAL LINK
   * ==========================================
   *
   * Example:
   *
   * /register?ref=USER_ID
   *
   * We store the USER_ID in referralCode.
   */

  const [
    searchParams,
  ] = useSearchParams();

  const referralCode =
    searchParams.get("ref") ||
    "";

  /**
   * ==========================================
   * REGISTER
   * ==========================================
   */

  const handleRegister = async (
    e?: React.MouseEvent<HTMLButtonElement>
  ): Promise<void> => {
    e?.preventDefault();

    // =========================
    // FULL NAME
    // =========================

    if (!fullName.trim()) {
      showToast(
        "Full Name is required.",
        "warning"
      );

      return;
    }

    // =========================
    // EMAIL
    // =========================

    if (!email.trim()) {
      showToast(
        "Email is required.",
        "warning"
      );

      return;
    }

    if (!email.includes("@")) {
      showToast(
        "Please enter a valid email address.",
        "warning"
      );

      return;
    }

    // =========================
    // PHONE
    // =========================

    if (!phoneNumber.trim()) {
      showToast(
        "Phone Number is required.",
        "warning"
      );

      return;
    }

    if (!/^\d+$/.test(phoneNumber)) {
      showToast(
        "Phone Number must contain only digits.",
        "warning"
      );

      return;
    }

    // =========================
    // SEX
    // =========================

    if (!chooseSex) {
      showToast(
        "Please select your sex.",
        "warning"
      );

      return;
    }

    // =========================
    // TERMS
    // =========================

    if (!acceptTerms) {
      showToast(
        "You must accept the Terms and Conditions.",
        "warning"
      );

      return;
    }

    // =========================
    // PASSWORD
    // =========================

    if (password.length < 6) {
      showToast(
        "Password must be at least 6 characters.",
        "warning"
      );

      return;
    }

    if (
      password !==
      confirmPassword
    ) {
      showToast(
        "Passwords do not match.",
        "error"
      );

      return;
    }

    // =========================
    // REGISTER USER
    // =========================

    const success =
      await register({
        fullName,

        email,

        phone:
          phoneNumber,

        password,

        confirmPassword,

        acceptTerms: true,

        /**
         * If the URL contains:
         *
         * ?ref=USER_ID
         *
         * send that ID to the backend.
         *
         * Otherwise send undefined.
         */

        referralCode:
          referralCode ||
          undefined,
      });

    // =========================
    // REGISTRATION FAILED
    // =========================

    if (!success) {
      showToast(
        "Unable to create account.",
        "error"
      );

      return;
    }

    // =========================
    // SUCCESS
    // =========================

    showToast(
      referralCode
        ? "Account created successfully through the referral link!"
        : "Account created successfully!",
      "success"
    );

    navigate("/");
  };

  return (
    <section className="py-16">
      <Container>
        <div className="max-w-md mx-auto">
          <SectionTitle
            title="Create Account"
            subtitle="Join MUHUZE Marketplace today."
          />

          <div className="space-y-5 mt-8">

            {/* Full Name */}

            <Input
              label="Full Name"
              type="text"
              placeholder="Enter your full name"
              value={fullName}
              onChange={(e) =>
                setFullName(
                  e.target.value
                )
              }
            />

            {/* Email */}

            <Input
              label="Email Address"
              type="email"
              placeholder="Enter your email address"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
            />

            {/* Phone */}

            <Input
              label="Phone Number"
              type="tel"
              placeholder="Enter your phone number"
              value={phoneNumber}
              onChange={(e) =>
                setPhoneNumber(
                  e.target.value
                )
              }
            />

            {/* Password */}

            <Input
              label="Password"
              type="password"
              placeholder="Create a password"
              value={password}
              onChange={(e) =>
                setPassword(
                  e.target.value
                )
              }
            />

            {/* Confirm Password */}

            <Input
              label="Confirm Password"
              type="password"
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) =>
                setConfirmPassword(
                  e.target.value
                )
              }
            />

            {/* Sex */}

            <div>
              <label className="block mb-2 font-medium text-gray-700">
                Sex
              </label>

              <select
                value={chooseSex}
                onChange={(e) =>
                  setChooseSex(
                    e.target.value
                  )
                }
                className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">
                  Select Sex
                </option>

                <option value="Male">
                  Male
                </option>

                <option value="Female">
                  Female
                </option>

                <option value="Both">
                  Both
                </option>
              </select>
            </div>

            {/* Referral Information */}

            {referralCode && (
              <div className="rounded-xl border border-green-200 bg-green-50 p-4">
                <p className="text-sm text-green-700">
                  You were invited through a MUHUZE referral link.
                </p>
              </div>
            )}

            {/* Terms */}

            <div className="flex items-start gap-3">
              <input
                id="terms"
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) =>
                  setAcceptTerms(
                    e.target.checked
                  )
                }
                className="mt-1 h-4 w-4 rounded border-gray-300"
              />

              <label
                htmlFor="terms"
                className="text-sm text-gray-700"
              >
                I agree to the

                <span className="font-semibold text-blue-600">
                  {" "}
                  Terms and Conditions
                </span>

                {" "}and{" "}

                <span className="font-semibold text-blue-600">
                  Privacy Policy
                </span>
                .
              </label>
            </div>

            {/* Registration Date */}

            <Input
              label="Registration Date"
              type="date"
              value={registerDate
                .toISOString()
                .split("T")[0]}
              onChange={(e) =>
                setRegisterDate(
                  new Date(
                    e.target.value
                  )
                )
              }
            />

            {/* Submit */}

            <Button
              className="w-full"
              onClick={
                handleRegister
              }
            >
              Create Account
            </Button>
          </div>
        </div>
      </Container>
    </section>
  );
}