import type { Camera } from "../../models/Camera";
import CameraCard from "./CameraCard";

interface Props {
  cameras: Camera[];
  onDelete: (id: number) => void;
}

export default function CameraGrid({ cameras, onDelete }: Props) {
  if (cameras.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-700 py-16 text-gray-500">
        <svg
          className="mb-4 h-16 w-16"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <p className="text-lg font-medium">No cameras added</p>
        <p className="text-sm">Add a camera to get started</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cameras.map((camera) => (
        <CameraCard key={camera.id} camera={camera} onDelete={onDelete} />
      ))}
    </div>
  );
}
