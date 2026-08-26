import StepCard from "./StepCard";
import { steps } from "./stepData";

export default function HowItWorks() {
  return (
    <section className="py-24 bg-white">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">
            How MUHUZE Works
          </h2>

          <p className="mt-5 text-gray-600 max-w-3xl mx-auto">
            Start buying and selling in just a few simple steps.
          </p>

        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10 mt-16">

          {steps.map((step) => (
            <StepCard
              key={step.id}
              step={step}
            />
          ))}

        </div>

      </div>

    </section>
  );
}