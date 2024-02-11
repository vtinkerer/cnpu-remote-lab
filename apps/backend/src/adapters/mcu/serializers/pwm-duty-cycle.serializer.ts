import { PWM } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWM)
export class PwmDutyCycleSerializer extends BaseMcuSerializer {
  key = 'PWMDC';

  extractValue(dto: PWM): string {
    return dto.pwmPercentage.toString();
  }
}
