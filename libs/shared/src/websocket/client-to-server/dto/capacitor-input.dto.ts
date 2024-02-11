import { ClientToServerDTO } from '../client-to-server.base';

export class CapacitorInput implements ClientToServerDTO {
  dtoName = CapacitorInput.name;
  // picoFarads

  readonly capacity: number;

  constructor({ capacity }: { capacity: number }) {
    this.capacity = capacity;
  }

  validate() {
    return (
      (this.capacity >= 0 && this.capacity <= 100_000_000) ||
      this.capacity === 0
    );
  }
}
