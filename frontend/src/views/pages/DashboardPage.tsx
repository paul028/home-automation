import { useState } from "react";
import { useCameraController } from "../../controllers/CameraController";
import CameraGrid from "../components/CameraGrid";
import AddCameraModal from "../components/AddCameraModal";

export default function DashboardPage() {
  const { cameras, locations, loading, error, addCamera, deleteCamera, updateCameraLocation } =
    useCameraController();
  const [showAddModal, setShowAddModal] = useState(false);

  const handleDelete = async (id: number) => {
    if (window.confirm("Are you sure you want to remove this camera?")) {
      await deleteCamera(id);
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Cameras</h2>
          <p className="text-sm text-gray-500">
            {cameras.length} camera{cameras.length !== 1 ? "s" : ""} configured
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
          Add Camera
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md border border-red-900 bg-red-900/20 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-600 border-t-blue-500" />
        </div>
      ) : (
        <CameraGrid
          cameras={cameras}
          onDelete={handleDelete}
          onUpdateLocation={updateCameraLocation}
          locations={locations}
        />
      )}

      <AddCameraModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={addCamera}
        locations={locations}
      />
    </div>
  );
}
