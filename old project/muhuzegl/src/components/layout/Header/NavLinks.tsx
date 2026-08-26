import { NavLink } from "react-router-dom";
import { navItems } from "./headerData";

export default function NavLinks() {
  return (
    <nav className="hidden lg:flex items-center gap-6">

      {navItems.map((item) => {
        const Icon = item.icon;
        const isSell = item.label === "Sell";
        const isPremium = item.label === "Premium";

        return (
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) =>
              `
                flex
                items-center
                gap-2
                font-medium
                transition-all
                duration-300
                ${
                  isSell
                    ? `
                      bg-orange-500
                      text-white
                      px-4
                      py-2
                      rounded-xl
                      hover:bg-orange-600
                      shadow-sm
                    `
                    : isPremium
                      ? `
                        text-orange-500
                        font-bold
                        hover:text-orange-600
                      `
                      : `
                        ${
                          isActive
                            ? "text-blue-600"
                            : "text-slate-700 hover:text-blue-600"
                        }
                      `
                }
              `
            }
          >
            <Icon className="text-sm" />

            {item.label}
          </NavLink>
        );
      })}

    </nav>
  );
}