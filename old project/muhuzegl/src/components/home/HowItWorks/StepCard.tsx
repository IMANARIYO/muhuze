import type { Step } from "./types";

interface Props {
  step: Step;
}

export default function StepCard({ step }: Props) {
  const Icon = step.icon;

  return (
    <div className="relative bg-white rounded-2xl shadow-lg p-8 text-center hover:-translate-y-2 hover:shadow-xl transition">

      <div className="absolute -top-5 left-1/2 -translate-x-1/2 bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center font-bold">
        {step.id}
      </div>

      <div className="flex justify-center mt-6">
        <div className="bg-blue-100 p-5 rounded-full text-blue-600">
          <Icon size={32} />
        </div>
      </div>

      <h3 className="mt-6 text-xl font-bold">
        {step.title}
      </h3>

      <p className="mt-4 text-gray-600">
        {step.description}
      </p>

    </div>
  );
}