import { Link } from "react-router-dom";
import type { Camera } from "../../models/Camera";

interface Props {
  camera: Camera;
  onDelete: (id: number) => void;
}

export default function CameraCard({ camera, onDelete }: Props) {
  return (
    <div className="overflow-hidden rounded-lg border border-gray-800 bg-gray-900 transition-colors hover:border-gray-700">
      <Link to={`/camera/${camera.id}`}>
        <div className="relative aspect-video bg-gray-800">
          <div className="flex h-full items-center justify-center text-gray-500">
            <svg
              className="h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div className="absolute bottom-2 left-2 flex gap-1">
            {camera.has_ptz && (
              <span className="rounded bg-blue-600/80 px-1.5 py-0.5 text-xs font-medium">
                PTZ
              </span>
            )}
            {camera.has_recording && (
              <span className="rounded bg-red-600/80 px-1.5 py-0.5 text-xs font-medium">
                REC
              </span>
            )}
          </div>
          <div
            className={`absolute right-2 top-2 h-2.5 w-2.5 rounded-full ${
              camera.is_active ? "bg-green-500" : "bg-red-500"
            }`}
          />
        </div>
      </Link>
      <div className="flex items-center justify-between p-3">
        <div>
          <h3 className="font-medium text-white">{camera.name}</h3>
          <p className="text-xs text-gray-500">
            {camera.ip_address} · {camera.model || camera.brand}
          </p>
        </div>
        <button
          onClick={() => onDelete(camera.id)}
          className="rounded p-1 text-gray-500 transition-colors hover:bg-red-900/30 hover:text-red-400"
          title="Delete camera"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
