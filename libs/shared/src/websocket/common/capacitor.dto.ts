import { BaseDto } from '../dto.base';

export const isCapacitorDto = (dto: unknown): dto is CapacitorDTO =>
  (dto as any).dtoName && (dto as any).dtoName === CapacitorDTO.name;

export class CapacitorDTO implements BaseDto {
  dtoName = CapacitorDTO.name;

  readonly capacity: number;

  constructor({ capacity }: { capacity: number }) {
    this.capacity = capacity;
  }
}
