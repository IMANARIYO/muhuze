import { FaGooglePlay, FaApple } from "react-icons/fa";
import FeatureItem from "./FeatureItem";
import { appFeatures } from "./appFeatures";

export default function DownloadApp() {
  return (
    <section className="py-24 bg-blue-700 text-white">

      <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">

        {/* Left */}

        <div>

          <h2 className="text-5xl font-bold">
            Download the MUHUZE App
          </h2>

          <p className="mt-6 text-blue-100 leading-8">

            Shop, sell, manage your wallet,
            receive notifications and chat
            with buyers or sellers directly
            from your smartphone.

          </p>

          <div className="mt-10 space-y-5">

            {appFeatures.map((feature) => (
              <FeatureItem
                key={feature.id}
                feature={feature}
              />
            ))}

          </div>

          <div className="flex flex-wrap gap-5 mt-12">

            <button className="flex items-center gap-3 bg-white text-black px-6 py-4 rounded-xl hover:scale-105 transition">

              <FaGooglePlay size={26} />

              <div className="text-left">

                <p className="text-xs">
                  GET IT ON
                </p>

                <strong>
                  Google Play
                </strong>

              </div>

            </button>

            <button className="flex items-center gap-3 bg-black text-white px-6 py-4 rounded-xl hover:scale-105 transition">

              <FaApple size={28} />

              <div className="text-left">

                <p className="text-xs">
                  Download on the
                </p>

                <strong>
                  App Store
                </strong>

              </div>

            </button>

          </div>

        </div>

        {/* Right */}

        <div className="flex justify-center">

          <div className="bg-white rounded-[40px] shadow-2xl w-72 h-[560px] p-5">

            <div className="bg-gray-200 rounded-[30px] w-full h-full flex items-center justify-center">

              <div className="text-center">

                <img
                  src="/images/logo.png"
                  alt="MUHUZE"
                  className="w-28 mx-auto"
                />

                <h3 className="mt-6 text-2xl font-bold text-blue-700">
                  MUHUZE
                </h3>

                <p className="mt-4 text-gray-600">
                  Mobile App Preview
                </p>

              </div>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}