import HeroContent from "./HeroContent";
import HeroImage from "./HeroImage";
import HeroStats from "./HeroStats";

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-slate-50">

      {/* Decorative background elements */}
      <div
        className="
          absolute
          -top-32
          -right-32
          w-96
          h-96
          rounded-full
          bg-blue-100/60
          blur-3xl
          pointer-events-none
        "
      />

      <div
        className="
          absolute
          -bottom-40
          -left-32
          w-96
          h-96
          rounded-full
          bg-orange-100/50
          blur-3xl
          pointer-events-none
        "
      />

      <div className="relative max-w-7xl mx-auto px-6 py-14 lg:py-24">

        {/* Main Hero */}
        <div
          className="
            grid
            lg:grid-cols-2
            gap-12
            lg:gap-20
            items-center
          "
        >

          <HeroContent />

          <HeroImage />

        </div>

        {/* Statistics */}
        <HeroStats />

      </div>
    </section>
  );
}