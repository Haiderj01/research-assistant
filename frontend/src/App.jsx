import { Routes, Route, Navigate } from "react-router-dom";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<div className="p-8 text-center text-lg">AI Research Assistant — Loading...</div>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
