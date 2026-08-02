import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import LoginModal from "../components/LoginModal";
import { useAppState, useAuthActions } from "../context/AppContext";

export default function AppLayout() {
  const { token, authModalOpen } = useAppState();
  const { closeAuthModal } = useAuthActions();

  const requiresLogin = !token || authModalOpen;

  return (
    <div className="flex h-screen bg-background text-primary">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
      <LoginModal
        open={requiresLogin}
        onClose={token ? closeAuthModal : () => {}}
      />
    </div>
  );
}
