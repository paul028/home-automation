import { useMemo } from "react";
import type { Camera } from "../../models/Camera";
import CameraCard from "./CameraCard";

interface Props {
  cameras: Camera[];
  onDelete: (id: number) => void;
  onUpdateLocation: (id: number, location: string) => void;
  locations: string[];
}

export default function CameraGrid({ cameras, onDelete, onUpdateLocation, locations }: Props) {
  const grouped = useMemo(() => {
    const groups: Record<string, Camera[]> = {};
    for (const camera of cameras) {
      const key = camera.location || "Ungrouped";
      if (!groups[key]) groups[key] = [];
      groups[key].push(camera);
    }
    // Sort: named locations first alphabetically, "Ungrouped" last
    const sorted = Object.entries(groups).sort(([a], [b]) => {
      if (a === "Ungrouped") return 1;
      if (b === "Ungrouped") return -1;
      return a.localeCompare(b);
    });
    return sorted;
  }, [cameras]);

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
    <div className="space-y-8">
      {grouped.map(([location, locationCameras]) => (
        <div key={location}>
          <h3 className="mb-3 text-sm font-medium uppercase tracking-wider text-gray-500">
            {location}
            <span className="ml-2 text-gray-600">
              ({locationCameras.length})
            </span>
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {locationCameras.map((camera) => (
              <CameraCard
                key={camera.id}
                camera={camera}
                onDelete={onDelete}
                onUpdateLocation={onUpdateLocation}
                locations={locations}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
