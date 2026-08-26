import type { WhyChoose } from "./types";

interface Props {
  item: WhyChoose;
}

export default function WhyChooseCard({
  item,
}: Props) {
  const Icon = item.icon;

  const isOrange = item.id % 2 === 0;

  return (
    <div
      className="
        group
        relative
        overflow-hidden
        rounded-3xl
        border
        border-slate-100
        bg-white
        p-8
        text-center
        shadow-sm
        transition-all
        duration-300
        hover:-translate-y-1
        hover:shadow-xl
      "
    >

      {/* ======================================
          DECORATIVE CORNER
      ====================================== */}

      <div
        className={`
          absolute
          -right-12
          -top-12
          h-32
          w-32
          rounded-full
          opacity-60
          transition
          duration-300
          group-hover:scale-110
          ${
            isOrange
              ? "bg-orange-100"
              : "bg-blue-100"
          }
        `}
      />

      {/* ======================================
          ICON
      ====================================== */}

      <div
        className={`
          relative
          mx-auto
          flex
          h-20
          w-20
          items-center
          justify-center
          rounded-2xl
          transition
          duration-300
          group-hover:scale-105
          ${
            isOrange
              ? "bg-orange-100"
              : "bg-blue-100"
          }
        `}
      >
        <Icon
          className={`
            text-4xl
            ${
              isOrange
                ? "text-orange-500"
                : "text-blue-600"
            }
          `}
        />
      </div>

      {/* ======================================
          TITLE
      ====================================== */}

      <h3
        className="
          relative
          mt-6
          text-xl
          font-bold
          text-slate-950
        "
      >
        {item.title}
      </h3>

      {/* ======================================
          DESCRIPTION
      ====================================== */}

      <p
        className="
          relative
          mt-4
          text-sm
          leading-7
          text-slate-600
        "
      >
        {item.description}
      </p>

      {/* ======================================
          BOTTOM ACCENT
      ====================================== */}

      <div
        className={`
          mx-auto
          mt-6
          h-1
          w-10
          rounded-full
          transition-all
          duration-300
          group-hover:w-16
          ${
            isOrange
              ? "bg-orange-500"
              : "bg-blue-600"
          }
        `}
      />

    </div>
  );
}