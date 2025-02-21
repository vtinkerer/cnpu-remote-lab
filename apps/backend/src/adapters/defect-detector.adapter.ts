import { IDefectDetectorAdapter } from '../core/interfaces/defect-detector-adapter.interface';
import { IMeasurementsRepository } from '../core/interfaces/measurements-repository.interface';
import fs from 'node:fs';

export class DefectDetectorAdapter implements IDefectDetectorAdapter {
  private serviceUrl = 'http://localhost:3801/analyze';

  constructor(
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async analyzeMeasurements(): Promise<{
    voltage_error_rms: number;
    current_error_rms: number;
    is_defective: boolean;
    voltage_error_percentage: number;
    current_error_percentage: number;
  }> {
    const measurements = this.measurementsRepository.getMeasurements();

    fs.writeFileSync(
      '/home/user1-44/measurements.json',
      JSON.stringify(measurements, null, 2)
    );

    const response = await fetch(this.serviceUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(measurements),
    });

    const result = await response.json();

    return result;
  }
}
