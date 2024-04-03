import { VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(VoltageOutputDto)
export class VoltageOutputSerializer extends BaseMcuSerializer {
  key = 'VOUT';

  extractValue(dto: VoltageOutputDto): string {
    return dto.voltage.toString();
  }
}
