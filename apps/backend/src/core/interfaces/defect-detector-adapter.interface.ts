import { DefectDetectorAnalysisResult } from '../entities/defect-detector-measurements.entity';
import { Measurements } from '../entities/measurements.entity';

export interface IDefectDetectorAdapter {
  analyzeMeasurements(): Promise<{
    result: DefectDetectorAnalysisResult;
    measurements: Measurements;
  }>;
}
