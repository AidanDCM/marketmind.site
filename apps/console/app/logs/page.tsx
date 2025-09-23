"use client";
import React from "react";
import { SystemAlerts } from "../../components/alerts/SystemAlerts";

export default function LogsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Logs & Alerts</h1>
      </div>
      <div className="bg-white border rounded-xl p-4">
        <SystemAlerts />
      </div>
    </div>
  );
}
