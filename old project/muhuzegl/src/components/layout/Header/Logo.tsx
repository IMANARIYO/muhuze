import { Link } from "react-router-dom";

export default function Logo() {
  return (
    <Link
      to="/"
      className="flex items-center shrink-0"
    >
      <img
        src="/images/logo/muhuzelogo2.png"
        alt="MUHUZE Global Link"
        className="
          h-14
          w-auto
          object-contain
        "
      />
    </Link>
  );
}