import { PWMDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWMDTO)
export class PwmDutyCycleSerializer extends BaseMcuSerializer {
  key = 'PWM';

  extractValue(dto: PWMDTO): string {
    if (dto.pwmPercentage > 100 || dto.pwmPercentage < 0) return;
    return dto.pwmPercentage.toFixed(2);
  }
}
