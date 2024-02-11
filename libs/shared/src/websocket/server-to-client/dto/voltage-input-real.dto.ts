import { ServerToClientDTO } from '../server-to-client.base';

export const isVoltageInputRealDto = (dto: unknown): dto is VoltageInputReal =>
  (dto as any).dtoName && (dto as any).dtoName === VoltageInputReal.name;

export class VoltageInputReal implements ServerToClientDTO {
  dtoName = VoltageInputReal.name;

  readonly voltage: number;

  constructor({ voltage }: { voltage: number }) {
    this.voltage = voltage;
  }
}
