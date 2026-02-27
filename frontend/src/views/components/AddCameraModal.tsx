import { useState } from "react";
import type { CameraCreate } from "../../models/Camera";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CameraCreate) => Promise<void>;
}

export default function AddCameraModal({ isOpen, onClose, onSubmit }: Props) {
  const [form, setForm] = useState<CameraCreate>({
    name: "",
    ip_address: "",
    username: "",
    password: "",
    model: "",
    brand: "tapo",
    has_ptz: false,
    has_recording: true,
  });
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit(form);
      setForm({
        name: "",
        ip_address: "",
        username: "",
        password: "",
        model: "",
        brand: "tapo",
        has_ptz: false,
        has_recording: true,
      });
      onClose();
    } catch {
      // Error handled by controller
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-lg border border-gray-800 bg-gray-900 p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Add Camera</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-white"
          >
            <svg
              className="h-5 w-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-gray-400">Name</label>
            <input
              type="text"
              required
              className={inputClass}
              placeholder="Living Room Camera"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">
              IP Address
            </label>
            <input
              type="text"
              required
              className={inputClass}
              placeholder="192.168.1.100"
              value={form.ip_address}
              onChange={(e) =>
                setForm({ ...form, ip_address: e.target.value })
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm text-gray-400">
                Username
              </label>
              <input
                type="text"
                required
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
                required
                className={inputClass}
                value={form.password}
                onChange={(e) =>
                  setForm({ ...form, password: e.target.value })
                }
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm text-gray-400">
              Model (optional)
            </label>
            <input
              type="text"
              className={inputClass}
              placeholder="C220, C520WS, etc."
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
          </div>

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
              Has PTZ controls
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-400">
              <input
                type="checkbox"
                checked={form.has_recording}
                onChange={(e) =>
                  setForm({ ...form, has_recording: e.target.checked })
                }
                className="rounded border-gray-700 bg-gray-800"
              />
              Has recording
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-4 py-2 text-sm text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {submitting ? "Adding..." : "Add Camera"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
