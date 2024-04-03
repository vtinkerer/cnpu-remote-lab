import { VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(VoltageOutputDto)
export class VoltageOutputSerializer extends BaseMcuSerializer {
  key = 'VOUT';

  extractValue(dto: VoltageOutputDto): string {
    if (dto.voltage > 100 || dto.voltage < 0) return;
    return dto.voltage.toFixed(1);
  }
}
