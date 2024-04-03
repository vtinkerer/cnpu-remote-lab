import { BaseDto } from '../dto.base';

export const isCurrentLoadDto = (dto: unknown): dto is CurrentLoadDTO =>
  (dto as any).dtoName && (dto as any).dtoName === CurrentLoadDTO.name;

export class CurrentLoadDTO implements BaseDto {
  dtoName = CurrentLoadDTO.name;

  readonly mA: number;

  constructor({ mA }: { mA: number }) {
    this.mA = mA;
  }
}
