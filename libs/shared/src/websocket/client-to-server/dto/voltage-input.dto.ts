import { ClientToServerDTO } from '../client-to-server.base';

export class VoltageInputDTO implements ClientToServerDTO {
  dtoName = VoltageInputDTO.name;

  readonly voltage: number;

  constructor({ voltage }: { voltage: number }) {
    this.voltage = voltage;
  }

  validate(): boolean {
    return (this.voltage > 0 && this.voltage <= 12) || this.voltage === 0;
  }
}
