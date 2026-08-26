import { useState } from "react";

interface FAQ {
  id: number;
  question: string;
  answer: string;
}

const faqs: FAQ[] = [
  {
    id: 1,
    question: "What is MUHUZE Premium?",
    answer:
      "MUHUZE Premium is a membership designed to give sellers additional business benefits, including increased product visibility, unlimited product listings, seller analytics, priority support, and access to selected Premium features.",
  },

  {
    id: 2,
    question: "How many products can Premium sellers list?",
    answer:
      "Premium members can create unlimited product listings, subject to MUHUZE marketplace rules and policies.",
  },

  {
    id: 3,
    question: "Can I change from Monthly to Annual?",
    answer:
      "Premium plans are currently available as separate Monthly and Annual memberships. If you already have an active Premium membership, you must wait until the current membership period ends before starting another Premium subscription.",
  },

  {
    id: 4,
    question: "What happens when Premium expires?",
    answer:
      "When your Premium membership expires, Premium benefits are no longer available. You can renew your membership to regain access to Premium features.",
  },

  {
    id: 5,
    question: "Does Premium include seller verification?",
    answer:
      "Premium membership provides seller verification eligibility. However, Premium membership itself does not guarantee verification. Sellers must meet MUHUZE verification requirements.",
  },

  {
    id: 6,
    question: "When can I renew my Premium membership?",
    answer:
      "You can renew your Premium membership after the current membership period has ended. Renewal options will be available when your current membership is no longer active.",
  },
];

export default function PremiumFAQ() {
  const [openId, setOpenId] = useState<number | null>(1);

  function toggle(id: number) {
    setOpenId((current) =>
      current === id ? null : id
    );
  }

  return (
    <section className="py-20">

      <div className="text-center mb-12">

        <h2 className="text-4xl font-bold">
          Frequently Asked Questions
        </h2>

        <p className="text-gray-500 mt-4">
          Everything you need to know about MUHUZE Premium.
        </p>

      </div>

      <div className="max-w-4xl mx-auto space-y-4">

        {faqs.map((faq) => (

          <div
            key={faq.id}
            className="bg-white rounded-xl shadow-md border overflow-hidden"
          >

            <button
              onClick={() => toggle(faq.id)}
              className="w-full flex justify-between items-center p-6 text-left"
            >

              <span className="font-semibold text-lg">
                {faq.question}
              </span>

              <span className="text-2xl">
                {openId === faq.id ? "−" : "+"}
              </span>

            </button>

            {openId === faq.id && (

              <div className="px-6 pb-6 text-gray-600 leading-7">

                {faq.answer}

              </div>

            )}

          </div>

        ))}

      </div>

    </section>
  );
}