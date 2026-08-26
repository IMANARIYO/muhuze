interface Props {

  title: string;

  subtitle?: string;
}

export default function SectionTitle({

  title,

  subtitle,

}: Props) {

  return (

    <div className="text-center mb-16">

      <h2 className="text-4xl font-bold">

        {title}

      </h2>

      {subtitle && (

        <p className="mt-5 text-gray-500 max-w-2xl mx-auto">

          {subtitle}

        </p>

      )}

    </div>

  );

}