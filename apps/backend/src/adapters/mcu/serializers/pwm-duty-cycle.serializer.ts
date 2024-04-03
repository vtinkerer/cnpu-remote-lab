import { PWMDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWMDTO)
export class PwmDutyCycleSerializer extends BaseMcuSerializer {
  key = 'PWM';

  extractValue(dto: PWMDTO): string {
    return dto.pwmPercentage.toString();
  }
}
