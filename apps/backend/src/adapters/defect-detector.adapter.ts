import { IDefectDetectorAdapter } from '../core/interfaces/defect-detector-adapter.interface';
import { IMeasurementsRepository } from '../core/interfaces/measurements-repository.interface';
import { Logger } from '../logger/logger';
import http from 'node:http';
import url from 'node:url';
import { DefectDetectorAnalysisResult } from '../core/entities/defect-detector-measurements.entity';
import { Measurements } from '../core/entities/measurements.entity';

function makeRequest(
  serviceUrl: string,
  measurements: any
): Promise<DefectDetectorAnalysisResult> {
  return new Promise((resolve, reject) => {
    const parsedUrl = url.parse(serviceUrl);
    const postData = JSON.stringify(measurements);

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port,
      path: parsedUrl.path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
    };

    const req = http.request(options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          resolve(result);
        } catch (error) {
          reject(new Error('Invalid JSON response: ' + error.message));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(postData);
    req.end();
  });
}

export class DefectDetectorAdapter implements IDefectDetectorAdapter {
  private logger = new Logger(DefectDetectorAdapter.name);

  private serviceUrl = 'http://localhost:3802/analyze';

  constructor(
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async analyzeMeasurements(): Promise<{
    result: DefectDetectorAnalysisResult;
    measurements: Measurements;
  }> {
    const measurements = this.measurementsRepository.getMeasurements();

    measurements.measurements.voltage = measurements.measurements.voltage.map(
      (v) => v * 1
    );

    this.logger.info({
      msg: 'Sending measurements to defect detector service',
      measurements,
    });

    const result = await makeRequest(this.serviceUrl, measurements);

    return {
      result,
      measurements,
    };
  }
}
