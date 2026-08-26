import FeatureCard from "./FeatureCard";
import { features } from "./featureData";

export default function WhyChooseUs() {
  return (
    <section className="py-24 bg-gray-50">

      <div className="max-w-7xl mx-auto px-6">

        <div className="text-center">

          <h2 className="text-4xl font-bold">
            Why Choose MUHUZE?
          </h2>

          <p className="mt-5 text-gray-600 max-w-3xl mx-auto">
            MUHUZE GLOBAL LINK is more than a marketplace.
            It is a trusted platform connecting buyers,
            sellers and businesses across Rwanda and East Africa.
          </p>

        </div>

        <div className="grid lg:grid-cols-3 md:grid-cols-2 gap-8 mt-16">

          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
            />
          ))}

        </div>

      </div>

    </section>
  );
}