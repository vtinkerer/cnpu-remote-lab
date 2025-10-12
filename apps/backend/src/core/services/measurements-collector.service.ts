import { IMeasurementsRepository } from '../interfaces/measurements-repository.interface';
import fs from 'node:fs';
import http from 'node:http';
import url from 'node:url';

function makeRequest(
  serviceUrl: string,
  measurements: any
): Promise<{
  voltage: number[];
  current: number[];
}> {
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

export class MeasurementsCollectorService {
  constructor(
    private readonly measurementsRepository: IMeasurementsRepository
  ) {}

  async run() {
    const measurements = await this.measurementsRepository.getMeasurements();

    const clearedMeasurements = await makeRequest(
      'http://localhost:3802/clear',
      measurements.measurements
    );

    const maxVBefore = Math.max(...measurements.measurements.voltage);
    const minVBefore = Math.min(...measurements.measurements.voltage);

    measurements.measurements.voltage = clearedMeasurements.voltage;
    measurements.measurements.current = clearedMeasurements.current;

    const maxV = Math.max(...measurements.measurements.voltage);
    const minV = Math.min(...measurements.measurements.voltage);
    const rippleV = maxV - minV;
    const meanV =
      measurements.measurements.voltage.reduce((acc, v) => acc + v, 0) /
      measurements.measurements.voltage.length;

    const maxI = Math.max(...measurements.measurements.current);
    const minI = Math.min(...measurements.measurements.current);
    const rippleI = maxI - minI;
    const meanI =
      measurements.measurements.current.reduce((acc, v) => acc + v, 0) /
      measurements.measurements.current.length;

    if (maxVBefore !== maxV || minVBefore !== minV) {
      console.log('Voltage changed after clearing:', {
        maxVBefore,
        minVBefore,
        maxV,
        minV,
      });
    } else {
      console.log('Voltage did not change after clearing');
    }

    fs.appendFileSync(
      `/home/user1-44/random-measurements.json`,
      JSON.stringify(
        {
          measurements,
          stats: {
            rippleV,
            meanV,
            rippleI,
            meanI,
          },
        },
        null
      ) + '\n'
    );
  }
}
