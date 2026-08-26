interface DashboardCardProps {
  title: string;
  value: string | number;
}

export default function DashboardCard({
  title,
  value,
}: DashboardCardProps) {
  return (
    <div
      className="
        bg-white
        rounded-xl
        shadow
        p-6
        border
      "
    >
      <p className="text-gray-500">
        {title}
      </p>

      <h2 className="text-3xl font-bold mt-3 text-blue-600">
        {value}
      </h2>
    </div>
  );
}