import { BrowserRouter, Routes, Route } from "react-router-dom";
import DashboardLayout from "./views/layouts/DashboardLayout";
import DashboardPage from "./views/pages/DashboardPage";
import CameraDetailPage from "./views/pages/CameraDetailPage";
import SettingsPage from "./views/pages/SettingsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/camera/:id" element={<CameraDetailPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
