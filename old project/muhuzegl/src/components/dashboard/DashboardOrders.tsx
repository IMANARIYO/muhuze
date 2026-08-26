import { Link } from "react-router-dom";

import { useOrders } from "../../context/OrderContext";

export default function DashboardOrders() {
  const { orders } = useOrders();

  const recentOrders = [...orders]
    .sort(
      (a, b) =>
        new Date(b.createdAt).getTime() -
        new Date(a.createdAt).getTime()
    )
    .slice(0, 5);

  return (
    <section className="mt-12">

      <div className="flex justify-between items-center mb-6">

        <h2 className="text-2xl font-bold">
          Recent Orders
        </h2>

        <Link
          to="/seller-orders"
          className="text-blue-600 font-semibold"
        >
          View All
        </Link>

      </div>

      <div className="bg-white rounded-3xl shadow-lg overflow-hidden">

        {recentOrders.length === 0 ? (
          <div className="p-10 text-center text-gray-500">
            No orders available.
          </div>
        ) : (
          <div className="overflow-x-auto">

            <table className="w-full">

              <thead className="bg-slate-100">

                <tr>

                  <th className="text-left p-5">
                    Buyer
                  </th>

                  <th className="text-left p-5">
                    Total
                  </th>

                  <th className="text-left p-5">
                    Status
                  </th>

                  <th className="text-left p-5">
                    Date
                  </th>

                </tr>

              </thead>

              <tbody>

                {recentOrders.map((order) => (
                  <tr
                    key={order._id}
                    className="border-b hover:bg-slate-50"
                  >
                    <td className="p-5">
                      {order.buyer}
                    </td>

                    <td className="p-5 font-semibold">
                      {order.total.toLocaleString()} RWF
                    </td>

                    <td className="p-5">
                      <span
                        className="
                          px-3
                          py-1
                          rounded-full
                          bg-blue-100
                          text-blue-700
                          text-sm
                        "
                      >
                        {order.status}
                      </span>
                    </td>

                    <td className="p-5 text-gray-500">
                      {new Date(
                        order.createdAt
                      ).toLocaleDateString()}
                    </td>
                  </tr>
                ))}

              </tbody>

            </table>

          </div>
        )}

      </div>

    </section>
  );
}