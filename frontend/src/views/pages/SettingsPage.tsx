import { useEffect, useState, useCallback } from "react";
import { cameraApi } from "../../services/api";
import type { Camera, CameraDetail, CameraUpdate } from "../../models/Camera";

interface CameraForm {
  ip_address: string;
  username: string;
  password: string;
  location: string;
  has_ptz: boolean;
  has_recording: boolean;
}

export default function SettingsPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<CameraForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchCameras = useCallback(async () => {
    try {
      const [cams, locs] = await Promise.all([
        cameraApi.getAll(),
        cameraApi.getLocations(),
      ]);
      setCameras(cams);
      setLocations(locs);
    } catch (err) {
      console.error("Failed to fetch cameras:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
  }, [fetchCameras]);

  const startEditing = async (camera: Camera) => {
    if (editingId === camera.id) {
      setEditingId(null);
      setForm(null);
      return;
    }
    setLoadingDetail(true);
    try {
      const detail: CameraDetail = await cameraApi.getById(camera.id);
      setEditingId(camera.id);
      setForm({
        ip_address: detail.ip_address,
        username: detail.username,
        password: "",
        location: detail.location || "",
        has_ptz: detail.has_ptz,
        has_recording: detail.has_recording,
      });
    } catch (err) {
      console.error("Failed to load camera details:", err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSave = async (cameraId: number) => {
    if (!form) return;
    setSaving(true);
    try {
      const update: CameraUpdate = {
        ip_address: form.ip_address,
        username: form.username,
        location: form.location || undefined,
        has_ptz: form.has_ptz,
        has_recording: form.has_recording,
      };
      if (form.password) {
        update.password = form.password;
      }
      await cameraApi.update(cameraId, update);
      setEditingId(null);
      setForm(null);
      await fetchCameras();
    } catch (err) {
      console.error("Failed to update camera:", err);
    } finally {
      setSaving(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none";

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-blue-500" />
      </div>
    );
  }

  return (
    <div>
      <h2 className="mb-6 text-2xl font-bold text-white">Settings</h2>

      <div className="rounded-lg border border-gray-800 bg-gray-900">
        <div className="border-b border-gray-800 px-6 py-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-gray-500">
            Cameras
          </h3>
        </div>

        {cameras.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-gray-500">
            No cameras configured
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {cameras.map((camera) => (
              <div key={camera.id}>
                <button
                  onClick={() => startEditing(camera)}
                  disabled={loadingDetail}
                  className="flex w-full items-center justify-between px-6 py-4 text-left transition-colors hover:bg-gray-800/50"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        camera.is_active ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <div>
                      <span className="text-sm font-medium text-white">
                        {camera.name}
                      </span>
                      <span className="ml-3 text-xs text-gray-500">
                        {camera.ip_address}
                      </span>
                    </div>
                  </div>
                  <svg
                    className={`h-4 w-4 text-gray-500 transition-transform ${
                      editingId === camera.id ? "rotate-180" : ""
                    }`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>

                {editingId === camera.id && form && (
                  <div className="border-t border-gray-800 bg-gray-950/50 px-6 py-5">
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label className="mb-1 block text-sm text-gray-400">
                          IP Address
                        </label>
                        <input
                          type="text"
                          className={inputClass}
                          value={form.ip_address}
                          onChange={(e) =>
                            setForm({ ...form, ip_address: e.target.value })
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm text-gray-400">
                          Location
                        </label>
                        <input
                          type="text"
                          list="settings-location-options"
                          className={inputClass}
                          placeholder="Living Room, Front Yard..."
                          value={form.location}
                          onChange={(e) =>
                            setForm({ ...form, location: e.target.value })
                          }
                        />
                        <datalist id="settings-location-options">
                          {locations.map((loc) => (
                            <option key={loc} value={loc} />
                          ))}
                        </datalist>
                      </div>
                      <div>
                        <label className="mb-1 block text-sm text-gray-400">
                          Username
                        </label>
                        <input
                          type="text"
                          className={inputClass}
                          value={form.username}
                          onChange={(e) =>
                            setForm({ ...form, username: e.target.value })
                          }
                        />
                      </div>
                      <div>
                        <label className="mb-1 block text-sm text-gray-400">
                          Password
                        </label>
                        <input
                          type="password"
                          className={inputClass}
                          placeholder="Leave blank to keep current"
                          value={form.password}
                          onChange={(e) =>
                            setForm({ ...form, password: e.target.value })
                          }
                        />
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between">
                      <div className="flex gap-6">
                        <label className="flex items-center gap-2 text-sm text-gray-400">
                          <input
                            type="checkbox"
                            checked={form.has_ptz}
                            onChange={(e) =>
                              setForm({ ...form, has_ptz: e.target.checked })
                            }
                            className="rounded border-gray-700 bg-gray-800"
                          />
                          PTZ Controls
                        </label>
                        <label className="flex items-center gap-2 text-sm text-gray-400">
                          <input
                            type="checkbox"
                            checked={form.has_recording}
                            onChange={(e) =>
                              setForm({
                                ...form,
                                has_recording: e.target.checked,
                              })
                            }
                            className="rounded border-gray-700 bg-gray-800"
                          />
                          Recording
                        </label>
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => {
                            setEditingId(null);
                            setForm(null);
                          }}
                          className="rounded-md px-4 py-2 text-sm text-gray-400 hover:text-white"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => handleSave(camera.id)}
                          disabled={saving}
                          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
                        >
                          {saving ? "Saving..." : "Save"}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
