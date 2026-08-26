import Skeleton from "./Skeleton";

export default function ProductSkeleton() {
  return (
    <div className="bg-white rounded-2xl shadow p-4">

      <Skeleton className="w-full h-56 rounded-xl" />

      <Skeleton className="h-6 w-3/4 mt-4" />

      <Skeleton className="h-5 w-1/2 mt-3" />

      <Skeleton className="h-5 w-2/3 mt-3" />

      <Skeleton className="h-10 w-full mt-6 rounded-xl" />

    </div>
  );
}