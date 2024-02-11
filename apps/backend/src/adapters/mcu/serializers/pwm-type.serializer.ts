import { PWMType } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWMType)
export class PwmTypeSerializer extends BaseMcuSerializer {
  key = 'PWMtype';

  extractValue(dto: PWMType): string {
    return dto.pwmType.toString();
  }
}
