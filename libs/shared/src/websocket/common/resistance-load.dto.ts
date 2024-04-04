import { BaseDto } from '../dto.base';

export const isResistanceLoadDto = (dto: unknown): dto is ResistanceLoadDTO =>
  (dto as any).dtoName && (dto as any).dtoName === ResistanceLoadDTO.name;

export class ResistanceLoadDTO implements BaseDto {
  readonly dtoName = ResistanceLoadDTO.name;

  readonly resistance: number;

  constructor({ resistance }: { resistance: number }) {
    this.resistance = resistance;
  }
}
