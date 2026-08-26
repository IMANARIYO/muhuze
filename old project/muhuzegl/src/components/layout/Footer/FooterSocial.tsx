import {
  FaFacebook,
  FaInstagram,
  FaLinkedin,
  FaYoutube,
} from "react-icons/fa";

export default function FooterSocial() {
  return (
    <div className="flex justify-center gap-5 text-2xl mt-6">

      <a href="#">
        <FaFacebook />
      </a>

      <a href="#">
        <FaInstagram />
      </a>

      <a href="#">
        <FaLinkedin />
      </a>

      <a href="#">
        <FaYoutube />
      </a>

    </div>
  );
}