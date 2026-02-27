export interface RecordingSegment {
  file_id: string;
  start_time: string;
  end_time: string;
  duration: number;
}

export interface RecordingDays {
  camera_id: number;
  year: number;
  month: number;
  days: number[];
}
