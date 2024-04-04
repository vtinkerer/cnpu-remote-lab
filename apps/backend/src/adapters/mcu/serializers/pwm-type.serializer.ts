import { PWMTypeDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(PWMTypeDTO)
export class PwmTypeSerializer extends BaseMcuSerializer {
  key = 'MODE';

  extractValue(dto: PWMTypeDTO): string {
    if (dto.type !== 'AUT' && dto.type !== 'MAN') return;
    return dto.type.toString();
  }
}
