import { PWMTypeDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWMTypeDTO)
export class PwmTypeSerializer extends BaseMcuSerializer {
  key = 'MODE';

  extractValue(dto: PWMTypeDTO): string {
    return dto.type.toString();
  }
}
