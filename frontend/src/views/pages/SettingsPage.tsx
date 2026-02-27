export default function SettingsPage() {
  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-white">Settings</h2>
      <div className="rounded-lg border border-gray-800 bg-gray-900 p-6">
        <p className="text-gray-400">
          Settings page coming soon. Here you'll be able to configure:
        </p>
        <ul className="mt-4 list-inside list-disc space-y-2 text-sm text-gray-500">
          <li>go2rtc connection settings</li>
          <li>Dashboard layout preferences</li>
          <li>Notification settings</li>
          <li>Future device integrations (LG Air Purifier, TCL Aircon, TCL TV)</li>
        </ul>
      </div>
    </div>
  );
}
