import { BaseDto } from '../dto.base';

export type SchemaType = 'BCK' | 'BST';

export const isSchemaTypeDto = (dto: unknown): dto is SchemaTypeDTO =>
  (dto as any).dtoName && (dto as any).dtoName === SchemaTypeDTO.name;

export class SchemaTypeDTO implements BaseDto {
  readonly dtoName = SchemaTypeDTO.name;

  readonly type: SchemaType;

  constructor({ type }: { type: SchemaType }) {
    this.type = type;
  }
}