import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";

export default function ProfileActions() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
  logout();
  navigate("/");
}
  if (!currentUser) {
    return null;
  }

  return (
    <div className="bg-white rounded-2xl shadow-md p-8">

      <h3 className="text-2xl font-bold mb-6">
        Quick Actions
      </h3>

      <div className="grid gap-4 md:grid-cols-2">

        <Link
          to="/profile/edit"
          className="bg-blue-600 text-white text-center py-3 rounded-xl hover:bg-blue-700 transition"
        >
          Edit Profile
        </Link>

        <Link
          to="/wallet"
          className="bg-green-600 text-white text-center py-3 rounded-xl hover:bg-green-700 transition"
        >
          My Wallet
        </Link>

        <Link
          to="/premium"
          className="bg-yellow-500 text-white text-center py-3 rounded-xl hover:bg-yellow-600 transition"
        >
          Premium Membership
        </Link>

        <Link
          to="/referral"
          className="bg-purple-600 text-white text-center py-3 rounded-xl hover:bg-purple-700 transition"
        >
          Referral Program
        </Link>

        {["seller", "admin"].includes(
  currentUser.role
) && (
          <Link
            to="/seller-dashboard"
            className="bg-indigo-600 text-white text-center py-3 rounded-xl hover:bg-indigo-700 transition"
          >
            Seller Dashboard
          </Link>
        )}

        <button
          onClick={handleLogout}
          className="bg-red-600 text-white py-3 rounded-xl hover:bg-red-700 transition"
        >
          Logout
        </button>

      </div>

    </div>
  );
}