import { VoltageInputDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(VoltageInputDTO)
export class InputVoltageSerializer extends BaseMcuSerializer {
  key = 'VIN';

  extractValue(dto: VoltageInputDTO): string {
    if (dto.voltage > 100 || dto.voltage < 0) return;
    return dto.voltage.toFixed(1);
  }
}
