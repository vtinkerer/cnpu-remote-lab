import { BaseDto } from '../../dto.base';

export type ScopeData = { voltage: number[]; time: string[] };

export const isScopeDataDto = (dto: unknown): dto is ScopeDataDTO =>
  (dto as any).dtoName && (dto as any).dtoName === ScopeDataDTO.name;

export class ScopeDataDTO implements BaseDto {
  dtoName = ScopeDataDTO.name;

  scopeData: ScopeData;

  constructor(scopeData: ScopeData) {
    this.scopeData = scopeData;
  }
}
