import { CurrentLoad } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CurrentLoad)
export class CurrentSerializer extends BaseMcuSerializer {
  key = 'Iload';

  extractValue(dto: CurrentLoad): string {
    return dto.mA.toFixed(0);
  }
}
