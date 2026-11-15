import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import { useAuth } from "./auth";
import Home from "./pages/Home";
import Listings from "./pages/Listings";
import ListingDetails from "./pages/ListingDetails";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Reservations from "./pages/Reservations";
import Dashboard from "./pages/Dashboard";
import NewListing from "./pages/NewListing";
import Admin from "./pages/Admin";

function RequireAuth({ children, role, admin, allowNoProfile }) {
  const { user, profile, loading } = useAuth();
  if (loading) return <p className="p-8 text-center text-gray-500">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (admin) return user.isAdmin ? children : <Navigate to="/" replace />;
  if (!profile && !allowNoProfile) return <Navigate to="/profile" replace />;
  if (role && profile.role !== role) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <div className="flex min-h-screen flex-col bg-gray-50 text-gray-900">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/listings" element={<Listings />} />
          <Route path="/listings/:id" element={<ListingDetails />} />
          <Route path="/login" element={<Login />} />
          <Route path="/profile" element={<RequireAuth allowNoProfile><Profile /></RequireAuth>} />
          <Route path="/reservations" element={<RequireAuth><Reservations /></RequireAuth>} />
          <Route path="/dashboard" element={<RequireAuth role="BUSINESS"><Dashboard /></RequireAuth>} />
          <Route path="/dashboard/new" element={<RequireAuth role="BUSINESS"><NewListing /></RequireAuth>} />
          <Route path="/admin" element={<RequireAuth admin><Admin /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="border-t bg-white py-6 text-center text-xs text-gray-500">
        FoodLoop · Buy Smart. Share Surplus. Waste Less. · Built on AWS Serverless
      </footer>
    </div>
  );
}
