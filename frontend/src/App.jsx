import { Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import AppLayout from "./layouts/AppLayout";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";
import ComparePage from "./pages/ComparePage";
import HistoryPage from "./pages/HistoryPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import OAuthCallbackPage from "./pages/OAuthCallbackPage";
import RequireAuth from "./components/RequireAuth";
import WelcomePage from "./pages/WelcomePage";

export default function App() {
  return (
    <AppProvider>
      <Routes>
        <Route path="/welcome" element={<WelcomePage />} />
        <Route index element={<WelcomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
        <Route element={<AppLayout />}>
          <Route path="upload" element={<UploadPage />} />
          <Route
            path="chat"
            element={
              <RequireAuth>
                <ChatPage />
              </RequireAuth>
            }
          />
          <Route
            path="compare"
            element={
              <RequireAuth>
                <ComparePage />
              </RequireAuth>
            }
          />
          <Route
            path="history"
            element={
              <RequireAuth>
                <HistoryPage />
              </RequireAuth>
            }
          />
          <Route
            path="dashboard"
            element={
              <RequireAuth>
                <DashboardPage />
              </RequireAuth>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppProvider>
  );
}
