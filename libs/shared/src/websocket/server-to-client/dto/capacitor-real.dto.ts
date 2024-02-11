import { ServerToClientDTO } from '../server-to-client.base';

export const isCapacitorRealDto = (dto: unknown): dto is CapacitorReal =>
  (dto as any).dtoName && (dto as any).dtoName === CapacitorReal.name;

export class CapacitorReal implements ServerToClientDTO {
  dtoName = CapacitorReal.name;

  // picoFarads
  readonly capacity: number;

  constructor({ capacity }: { capacity: number }) {
    this.capacity = capacity;
  }
}
