import { ClientToServerDTO } from '@cnpu-remote-lab-nx/shared';

export abstract class BaseMcuSerializer<
  T extends ClientToServerDTO = ClientToServerDTO
> {
  abstract key: string;

  abstract extractValue(dto: T): string;

  serialize(dto: T) {
    return `${this.key}=${this.extractValue(dto)};`;
  }
}

export const serializers: Record<string, BaseMcuSerializer> = {};

export function McuSerializer(dtoClass: { name: string }) {
  return function <T extends { new (...args: any[]): BaseMcuSerializer }>(
    Target: T
  ) {
    serializers[dtoClass.name] = new Target();
  };
}
