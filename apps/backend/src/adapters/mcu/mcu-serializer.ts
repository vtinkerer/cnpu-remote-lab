import { BaseDto } from '@cnpu-remote-lab-nx/shared';

export abstract class BaseMcuSerializer<T extends BaseDto = BaseDto> {
  abstract key: string;

  abstract extractValue(dto: T): string;

  serialize(dto: T) {
    return `${this.key}=${this.extractValue(dto)};\n`;
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
