import { CapacitorDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CapacitorDTO)
export class CapasitorSerializer extends BaseMcuSerializer {
  key = 'C';

  extractValue(dto: CapacitorDTO): string {
    return dto.capacity.toFixed(2);
  }
}
