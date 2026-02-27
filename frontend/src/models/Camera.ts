export interface Camera {
  id: number;
  name: string;
  ip_address: string;
  model: string | null;
  location: string | null;
  brand: string;
  has_ptz: boolean;
  has_recording: boolean;
  is_active: boolean;
}

export interface CameraDetail extends Camera {
  username: string;
}

export interface CameraCreate {
  name: string;
  ip_address: string;
  username: string;
  password: string;
  model?: string;
  location?: string;
  brand?: string;
  has_ptz?: boolean;
  has_recording?: boolean;
}

export interface CameraUpdate {
  name?: string;
  ip_address?: string;
  username?: string;
  password?: string;
  model?: string;
  location?: string;
  has_ptz?: boolean;
  has_recording?: boolean;
  is_active?: boolean;
}
