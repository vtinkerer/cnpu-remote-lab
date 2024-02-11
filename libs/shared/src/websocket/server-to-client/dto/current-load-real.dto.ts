import { ServerToClientDTO } from '../server-to-client.base';

export const isCurrentLoadRealDto = (dto: unknown): dto is CurrentLoadReal =>
  (dto as any).dtoName && (dto as any).dtoName === CurrentLoadReal.name;

export class CurrentLoadReal implements ServerToClientDTO {
  dtoName = CurrentLoadReal.name;

  readonly mA: number;

  constructor({ mA }: { mA: number }) {
    this.mA = mA;
  }
}
