import { Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import AppLayout from "./layouts/AppLayout";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";
import HistoryPage from "./pages/HistoryPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <AppProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<UploadPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="dashboard" element={<DashboardPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppProvider>
  );
}
