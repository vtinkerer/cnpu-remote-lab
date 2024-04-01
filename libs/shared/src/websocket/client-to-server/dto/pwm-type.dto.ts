import { ClientToServerDTO } from '../client-to-server.base';

export type TPwmType = 'auto' | 'manual';

export const isPWMTypeDto = (dto: unknown): dto is PWMType =>
  (dto as any).dtoName && (dto as any).dtoName === PWMType.name;

export class PWMType implements ClientToServerDTO {
  dtoName = PWMType.name;

  pwmType: TPwmType;

  constructor({ pwmType }: { pwmType: TPwmType }) {
    this.pwmType = pwmType;
  }

  validate(): boolean {
    return this.pwmType === 'auto' || this.pwmType === 'manual';
  }
}
