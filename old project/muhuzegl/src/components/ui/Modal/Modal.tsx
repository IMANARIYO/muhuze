import { useEffect } from "react";
import { FaTimes } from "react-icons/fa";

import type { ModalProps } from "./types";

export default function Modal({
  isOpen,
  title,
  children,
  onClose,
  closeOnOverlayClick = true,
}: ModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleEscape);

    return () =>
      window.removeEventListener(
        "keydown",
        handleEscape
      );
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="
        fixed
        inset-0
        bg-black/60
        flex
        items-center
        justify-center
        p-4
        z-50
        animate-fadeIn
      "
      onClick={() => {
        if (closeOnOverlayClick) {
          onClose();
        }
      }}
    >
      <div
        className="
          bg-white
          rounded-3xl
          shadow-2xl
          w-full
          max-w-xl
          overflow-hidden
          animate-scaleIn
        "
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}

        <div
          className="
            flex
            items-center
            justify-between
            border-b
            px-6
            py-5
          "
        >
          <h2 className="text-2xl font-bold">
            {title}
          </h2>

          <button
            onClick={onClose}
            className="
              w-10
              h-10
              rounded-full
              flex
              items-center
              justify-center
              hover:bg-red-100
              hover:text-red-600
              transition
            "
          >
            <FaTimes />
          </button>
        </div>

        {/* Body */}

        <div className="p-6">
          {children}
        </div>

      </div>
    </div>
  );
}