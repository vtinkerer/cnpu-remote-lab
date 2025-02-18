import { IDefectDetectorAdapter } from '../core/interfaces/defect-detector-adapter.interface';
import { IMeasurementsRepository } from '../core/interfaces/measurements-repository.interface';

export class DefectDetectorAdapter implements IDefectDetectorAdapter {
  private serviceUrl = 'http://localhost:3801/analyze';

  constructor(
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async analyzeMeasurements(): Promise<{
    voltage_error_rms: number;
    current_error_rms: number;
    is_defective: boolean;
  }> {
    const measurements = this.measurementsRepository.getMeasurements();

    const response = await fetch(this.serviceUrl, {
      method: 'POST',
      body: JSON.stringify(measurements),
    });

    const result = await response.json();

    return {
      voltage_error_rms: result?.voltage_error_rms,
      current_error_rms: result?.current_error_rms,
      is_defective: result?.is_defective,
    };
  }
}
