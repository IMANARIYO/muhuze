import { Link } from "react-router-dom";
import type { FooterSection } from "./types";
import { FaAngleRight } from "react-icons/fa";

interface Props {
  section: FooterSection;
}

export default function FooterColumn({
  section,
}: Props) {
  return (
    <div>

      <h3 className="mb-5 text-lg font-bold text-white">
        {section.title}
      </h3>

      <ul className="space-y-3">

        {section.links.map((link) => (

          <li key={link.label}>

            <Link
              to={link.path}
              className="
                group
                flex
                items-center
                gap-2
                text-slate-400
                transition-all
                duration-300
                hover:translate-x-1
                hover:text-blue-400
              "
            >

              <FaAngleRight
                className="
                  text-xs
                  text-orange-500
                  transition
                  group-hover:text-orange-400
                "
              />

              {link.label}

            </Link>

          </li>

        ))}

      </ul>

    </div>
  );
}