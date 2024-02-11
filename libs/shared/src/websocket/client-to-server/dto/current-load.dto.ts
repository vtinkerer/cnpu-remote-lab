import { ClientToServerDTO } from '../client-to-server.base';

export class CurrentLoad implements ClientToServerDTO {
  dtoName = CurrentLoad.name;

  readonly mA: number;
  constructor({ mA }: { mA: number }) {
    this.mA = mA;
  }

  validate(): boolean {
    return (this.mA > 0 && this.mA <= 2000) || this.mA === 0;
  }
}
