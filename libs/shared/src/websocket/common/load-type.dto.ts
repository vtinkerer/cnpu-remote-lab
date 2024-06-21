import { BaseDto } from '../dto.base';

export type LoadType = 'CUR' | 'RES';

export const isLoadTypeDto = (dto: unknown): dto is LoadTypeDTO =>
  (dto as any).dtoName && (dto as any).dtoName === LoadTypeDTO.name;

export class LoadTypeDTO implements BaseDto {
  readonly dtoName = LoadTypeDTO.name;

  readonly type: LoadType;

  constructor({ type }: { type: LoadType }) {
    this.type = type;
  }
}
