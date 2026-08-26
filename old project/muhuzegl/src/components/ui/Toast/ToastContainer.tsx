import Toast from "./Toast";
import type { Toast as ToastType } from "./types";

interface Props {
  toasts: ToastType[];
}

export default function ToastContainer({
  toasts,
}: Props) {
  return (
    <div
      className="
        fixed
        top-6
        right-6
        z-50
        flex
        flex-col
        gap-4
      "
    >
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          toast={toast}
        />
      ))}
    </div>
  );
}