import { BaseDto } from '../dto.base';

export type PWMType = 'MAN' | 'AUT';

export const isPWMTypeDto = (dto: unknown): dto is PWMTypeDTO =>
  (dto as any).dtoName && (dto as any).dtoName === PWMTypeDTO.name;

export class PWMTypeDTO implements BaseDto {
  readonly dtoName = PWMTypeDTO.name;

  readonly type: PWMType;

  constructor({ type }: { type: PWMType }) {
    this.type = type;
  }
}
