export interface IDefectDetectorAdapter {
  analyzeMeasurements(): Promise<{
    voltage_error_rms: number;
    current_error_rms: number;
    is_defective: boolean;
  }>;
}
