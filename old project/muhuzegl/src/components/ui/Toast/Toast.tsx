import {
  FaCheckCircle,
  FaExclamationCircle,
  FaExclamationTriangle,
  FaInfoCircle,
} from "react-icons/fa";

import type { Toast } from "./types";

interface Props {
  toast: Toast;
}

export default function Toast({ toast }: Props) {
  const styles = {
    success: {
      bg: "bg-green-600",
      icon: <FaCheckCircle />,
    },
    error: {
      bg: "bg-red-600",
      icon: <FaExclamationCircle />,
    },
    warning: {
      bg: "bg-yellow-500",
      icon: <FaExclamationTriangle />,
    },
    info: {
      bg: "bg-blue-600",
      icon: <FaInfoCircle />,
    },
  };

  return (
    <div
      className={`
        ${styles[toast.type].bg}
        text-white
        px-6
        py-4
        rounded-xl
        shadow-xl
        flex
        items-center
        gap-3
        min-w-[320px]
      `}
    >
      <span className="text-xl">
        {styles[toast.type].icon}
      </span>

      <span>{toast.message}</span>
    </div>
  );
}