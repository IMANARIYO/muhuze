import { forwardRef } from "react";
import { inputVariants } from "./inputVariants";

interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;

  error?: string;

  variant?: "default" | "success" | "error";
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      variant = "default",
      className = "",
      ...props
    },
    ref
  ) => {
    return (
      <div className="w-full">

        {label && (
          <label className="block mb-2 font-medium text-gray-700">
            {label}
          </label>
        )}

        <input
          ref={ref}
          className={`
            w-full
            rounded-xl
            border
            px-4
            py-3
            outline-none
            transition
            focus:ring-2
            ${inputVariants[variant]}
            ${className}
          `}
          {...props}
        />

        {error && (
          <p className="mt-2 text-sm text-red-600">
            {error}
          </p>
        )}

      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;