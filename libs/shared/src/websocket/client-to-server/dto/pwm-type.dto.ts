import { ClientToServerDTO } from '../client-to-server.base';

export type TPwmType = 'auto' | 'manual';

export class PWMType implements ClientToServerDTO {
  dtoName = PWMType.name;

  readonly pwmType: TPwmType;

  constructor({ pwmType }: { pwmType: TPwmType }) {
    this.pwmType = pwmType;
  }

  validate(): boolean {
    return this.pwmType === 'auto' || this.pwmType === 'manual';
  }
}
