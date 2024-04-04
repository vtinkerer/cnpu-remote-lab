import { CapacitorDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CapacitorDTO)
export class CapasitorSerializer extends BaseMcuSerializer {
  key = 'C';

  extractValue(dto: CapacitorDTO): string {
    if (dto.capacity > 1000 || dto.capacity < 0) return;
    return dto.capacity.toFixed(0);
  }
}
