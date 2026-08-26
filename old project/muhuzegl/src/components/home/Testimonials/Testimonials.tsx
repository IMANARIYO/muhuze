import TestimonialCard from "./TestimonialCard";
import { testimonials } from "./testimonialData";

export default function Testimonials() {
  return (
    <section
      className="
        bg-slate-50
        py-16
        lg:py-20
      "
    >
      <div className="mx-auto max-w-7xl px-6">

        {/* ======================================
            SECTION HEADER
        ====================================== */}

        <div className="mx-auto max-w-3xl text-center">

          <span
            className="
              font-semibold
              uppercase
              tracking-[0.2em]
              text-blue-600
            "
          >
            Testimonials
          </span>

          <h2
            className="
              mt-4
              text-4xl
              font-extrabold
              tracking-tight
              text-slate-950
              lg:text-5xl
            "
          >
            What Our Users
            <span className="text-orange-500">
              {" "}Say
            </span>
          </h2>

          <p
            className="
              mx-auto
              mt-5
              max-w-2xl
              text-lg
              leading-8
              text-slate-600
            "
          >
            Hear from buyers, sellers and affiliates
            who are using MUHUZE to discover
            opportunities and grow.
          </p>

        </div>

        {/* ======================================
            TESTIMONIALS
        ====================================== */}

        <div
          className="
            mt-12
            grid
            grid-cols-1
            gap-6
            md:grid-cols-2
            lg:grid-cols-3
          "
        >
          {testimonials.map((testimonial) => (
            <TestimonialCard
              key={testimonial.id}
              testimonial={testimonial}
            />
          ))}
        </div>

      </div>
    </section>
  );
}