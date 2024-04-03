import { BaseDto } from '../../dto.base';

export type ScopePoint = {
  t: string;
  v: number;
};

export type ScopeData = ScopePoint[];

export const isScopeDataDto = (dto: unknown): dto is ScopeDataDTO =>
  (dto as any).dtoName && (dto as any).dtoName === ScopeDataDTO.name;

export class ScopeDataDTO implements BaseDto {
  dtoName = ScopeDataDTO.name;

  scopeData: ScopeData;

  constructor(scopeData: ScopeData) {
    this.scopeData = scopeData;
  }
}
