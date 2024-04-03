import { BaseDto } from '../dto.base';

export const isVoltageOutputDto = (dto: unknown): dto is VoltageOutputDto =>
  (dto as any).dtoName && (dto as any).dtoName === VoltageOutputDto.name;

export class VoltageOutputDto implements BaseDto {
  dtoName = VoltageOutputDto.name;

  readonly voltage: number;

  constructor({ voltage }: { voltage: number }) {
    this.voltage = voltage;
  }
}
