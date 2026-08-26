import Logo from "./Logo";
import SearchBar from "./SearchBar";
import NavLinks from "./NavLinks";
import UserMenu from "./UserMenu";
import MobileMenu from "./MobileMenu";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white shadow-md">

<div
  className="
    max-w-7xl
    mx-auto
    px-4
    sm:px-6
    lg:px-8
    h-20
    flex
    items-center
    justify-between
    gap-4
  "
>
        <Logo />

        <SearchBar />

        <NavLinks />

        <UserMenu />

        <MobileMenu />

      </div>

    </header>
  );
}