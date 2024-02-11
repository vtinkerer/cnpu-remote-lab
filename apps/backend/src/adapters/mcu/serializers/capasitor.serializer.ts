import { CapacitorInput } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CapacitorInput)
export class CapasitorSerializer extends BaseMcuSerializer {
  key = 'Cf';

  extractValue(dto: CapacitorInput): string {
    return dto.capacity.toFixed(2);
  }
}
