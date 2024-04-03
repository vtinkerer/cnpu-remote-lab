import { BaseDto } from '../dto.base';

export const isPWMDto = (dto: unknown): dto is PWMDTO =>
  (dto as any).dtoName && (dto as any).dtoName === PWMDTO.name;

export class PWMDTO implements BaseDto {
  dtoName = PWMDTO.name;

  readonly pwmPercentage: number;

  constructor({ pwmPercentage }: { pwmPercentage: number }) {
    this.pwmPercentage = pwmPercentage;
  }
}
