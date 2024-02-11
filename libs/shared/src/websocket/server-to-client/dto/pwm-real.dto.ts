import { ServerToClientDTO } from '../server-to-client.base';

export const isPWMRealDto = (dto: unknown): dto is PWMReal =>
  (dto as any).dtoName && (dto as any).dtoName === PWMReal.name;

export class PWMReal implements ServerToClientDTO {
  dtoName = PWMReal.name;

  // Value between 0 and 100
  readonly pwmPercentage: number;

  constructor({ pwmPercentage }: { pwmPercentage: number }) {
    this.pwmPercentage = pwmPercentage;
  }
}
