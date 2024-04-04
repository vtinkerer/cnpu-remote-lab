import { BaseDto } from '../dto.base';

export const isVoltageInputDto = (dto: unknown): dto is VoltageInputDTO =>
  (dto as any).dtoName && (dto as any).dtoName === VoltageInputDTO.name;

export class VoltageInputDTO implements BaseDto {
  dtoName = VoltageInputDTO.name;

  readonly voltage: number;

  constructor({ voltage }: { voltage: number }) {
    this.voltage = voltage;
  }
}
