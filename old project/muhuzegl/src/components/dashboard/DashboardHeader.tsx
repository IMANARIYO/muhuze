import { FaStore } from "react-icons/fa";

export default function DashboardHeader() {
  const currentUser = JSON.parse(
    localStorage.getItem("currentUser") || "null"
  );

  return (
    <div className="bg-gradient-to-r from-blue-700 to-indigo-700 rounded-3xl text-white p-8">

      <div className="flex items-center gap-5">

        <div className="w-20 h-20 rounded-full bg-white text-blue-700 flex items-center justify-center">

          <FaStore className="text-4xl" />

        </div>

        <div>

          <h1 className="text-4xl font-bold">
            Seller Dashboard
          </h1>

          <p className="mt-2 text-blue-100">
            Welcome back,
            {" "}
            {currentUser?.fullName ??
              "Seller"}
          </p>

        </div>

      </div>

    </div>
  );
}