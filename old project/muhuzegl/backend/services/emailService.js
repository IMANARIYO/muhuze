import nodemailer from "nodemailer";

/**
 * ==========================================
 * EMAIL TRANSPORTER
 * ==========================================
 */

const transporter =
  nodemailer.createTransport({
    service: "gmail",

    auth: {
      user:
        process.env.EMAIL_USER,

      pass:
        process.env.EMAIL_APP_PASSWORD,
    },
  });

/**
 * ==========================================
 * SEND PASSWORD RESET EMAIL
 * ==========================================
 */

const sendPasswordResetEmail = async ({
  email,
  resetUrl,
}) => {
  if (!email) {
    throw new Error(
      "Recipient email is required."
    );
  }

  if (!resetUrl) {
    throw new Error(
      "Password reset URL is required."
    );
  }

  await transporter.sendMail({
    from: `"MUHUZE Global Link" <${process.env.EMAIL_USER}>`,

    to: email,

    subject:
      "MUHUZE - Reset Your Password",

    text: `
Hello,

You requested to reset your MUHUZE password.

Click the link below to create a new password:

${resetUrl}

This password reset link will expire in 30 minutes.

If you did not request this password reset, you can safely ignore this email.

Regards,
MUHUZE Global Link
    `,

    html: `
      <div style="
        font-family: Arial, sans-serif;
        max-width: 600px;
        margin: 0 auto;
        padding: 30px;
        background: #f5f5f5;
      ">

        <div style="
          background: white;
          padding: 30px;
          border-radius: 12px;
        ">

          <h1 style="
            color: #1d4ed8;
            margin-bottom: 10px;
          ">
            MUHUZE
          </h1>

          <p style="
            color: #666;
            margin-top: 0;
          ">
            Global Link Marketplace
          </p>

          <h2>
            Reset Your Password
          </h2>

          <p>
            We received a request to reset
            your MUHUZE account password.
          </p>

          <p>
            Click the button below to create
            a new password:
          </p>

          <div style="
            margin: 30px 0;
          ">

            <a
              href="${resetUrl}"
              style="
                display: inline-block;
                background: #2563eb;
                color: white;
                text-decoration: none;
                padding: 14px 24px;
                border-radius: 8px;
                font-weight: bold;
              "
            >
              Reset Password
            </a>

          </div>

          <p>
            This link will expire in
            <strong>30 minutes</strong>.
          </p>

          <p style="
            color: #666;
            font-size: 14px;
          ">
            If you did not request a password
            reset, you can safely ignore this
            email.
          </p>

          <hr />

          <p style="
            color: #999;
            font-size: 12px;
          ">
            MUHUZE Global Link
          </p>

        </div>

      </div>
    `,
  });
};
/**
 * ==========================================
 * SEND EMAIL VERIFICATION EMAIL
 * ==========================================
 */

const sendEmailVerificationEmail = async ({
  email,
  verificationUrl,
}) => {
  if (!email) {
    throw new Error(
      "Recipient email is required."
    );
  }

  if (!verificationUrl) {
    throw new Error(
      "Email verification URL is required."
    );
  }

  await transporter.sendMail({
    from: `"MUHUZE Global Link" <${process.env.EMAIL_USER}>`,

    to: email,

    subject:
      "MUHUZE - Verify Your Email",

    text: `
Hello,

Welcome to MUHUZE Global Link.

Please verify your email address by clicking the link below:

${verificationUrl}

This verification link will expire in 30 minutes.

If you did not create a MUHUZE account, you can safely ignore this email.

Regards,
MUHUZE Global Link
    `,

    html: `
      <div style="
        font-family: Arial, sans-serif;
        max-width: 600px;
        margin: 0 auto;
        padding: 30px;
        background: #f5f5f5;
      ">

        <div style="
          background: white;
          padding: 30px;
          border-radius: 12px;
        ">

          <h1 style="
            color: #1d4ed8;
            margin-bottom: 10px;
          ">
            MUHUZE
          </h1>

          <p style="
            color: #666;
            margin-top: 0;
          ">
            Global Link Marketplace
          </p>

          <h2>
            Verify Your Email
          </h2>

          <p>
            Welcome to MUHUZE Global Link.
          </p>

          <p>
            Please verify your email address
            to activate your account.
          </p>

          <div style="
            margin: 30px 0;
          ">

            <a
              href="${verificationUrl}"
              style="
                display: inline-block;
                background: #2563eb;
                color: white;
                text-decoration: none;
                padding: 14px 24px;
                border-radius: 8px;
                font-weight: bold;
              "
            >
              Verify My Email
            </a>

          </div>

          <p>
            This verification link will expire
            in <strong>30 minutes</strong>.
          </p>

          <p style="
            color: #666;
            font-size: 14px;
          ">
            If you did not create a MUHUZE
            account, you can safely ignore
            this email.
          </p>

          <hr />

          <p style="
            color: #999;
            font-size: 12px;
          ">
            MUHUZE Global Link
          </p>

        </div>

      </div>
    `,
  });
};

export default {
  sendPasswordResetEmail,
  sendEmailVerificationEmail,
};