import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
