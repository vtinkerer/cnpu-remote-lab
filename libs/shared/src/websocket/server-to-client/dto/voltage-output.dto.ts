import { ServerToClientDTO } from '../server-to-client.base';

export const isVoltageOutputDto = (dto: unknown): dto is VoltageOutputDto =>
  (dto as any).dtoName && (dto as any).dtoName === VoltageOutputDto.name;

export class VoltageOutputDto implements ServerToClientDTO {
  dtoName = VoltageOutputDto.name;

  voltage: number;

  constructor({ voltage }: { voltage: number }) {
    this.voltage = voltage;
  }
}
