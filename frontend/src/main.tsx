import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import "./index.css";
import Assistant from "./pages/Assistant";
import Classifier from "./pages/Classifier";
import Compliance from "./pages/Compliance";
import Dashboard from "./pages/Dashboard";
import DutyCalculator from "./pages/DutyCalculator";
import ShipmentDetail from "./pages/ShipmentDetail";
import Shipments from "./pages/Shipments";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="shipments" element={<Shipments />} />
          <Route path="shipments/:id" element={<ShipmentDetail />} />
          <Route path="classifier" element={<Classifier />} />
          <Route path="duty" element={<DutyCalculator />} />
          <Route path="compliance" element={<Compliance />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="*" element={<p className="text-slate-500">Page not found.</p>} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
