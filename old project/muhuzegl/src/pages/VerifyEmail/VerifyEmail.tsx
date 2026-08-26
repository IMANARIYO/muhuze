import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

export default function VerifyEmail() {
  const { token } = useParams();

  const [status, setStatus] =
    useState<
      "loading" | "success" | "error"
    >("loading");

  const [message, setMessage] =
    useState("");

  useEffect(() => {
    async function verify() {
      if (!token) {
        setStatus("error");
        setMessage(
          "Verification token is missing."
        );
        return;
      }

      try {
        const response =
          await fetch(
            `http://localhost:5000/api/users/verify-email/${token}`
          );

        const result =
          await response.json();

        if (!response.ok) {
          throw new Error(
            result.message ||
              "Email verification failed."
          );
        }

        setStatus("success");

        setMessage(
          result.message ||
            "Your email has been verified successfully."
        );

      } catch (error) {
        setStatus("error");

        setMessage(
          error instanceof Error
            ? error.message
            : "Email verification failed."
        );
      }
    }

    verify();
  }, [token]);

  return (
    <section className="min-h-[60vh] flex items-center justify-center px-4">

      <div className="w-full max-w-lg bg-white rounded-2xl shadow-md p-8 text-center">

        {status === "loading" && (
          <>
            <h1 className="text-2xl font-bold">
              Verifying Your Email
            </h1>

            <p className="text-gray-500 mt-3">
              Please wait...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <h1 className="text-2xl font-bold text-green-600">
              Email Verified!
            </h1>

            <p className="text-gray-600 mt-3">
              {message}
            </p>

            <Link
              to="/login"
              className="inline-block mt-6 bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700"
            >
              Go to Login
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <h1 className="text-2xl font-bold text-red-600">
              Verification Failed
            </h1>

            <p className="text-gray-600 mt-3">
              {message}
            </p>

            <Link
              to="/login"
              className="inline-block mt-6 bg-gray-800 text-white px-6 py-3 rounded-xl hover:bg-gray-900"
            >
              Go to Login
            </Link>
          </>
        )}

      </div>

    </section>
  );
}