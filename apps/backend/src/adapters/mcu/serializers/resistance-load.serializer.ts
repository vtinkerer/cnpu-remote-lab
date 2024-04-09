import { ResistanceLoadDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(ResistanceLoadDTO)
export class ResistanceLoadSerializer extends BaseMcuSerializer {
  key = 'RL';

  extractValue(dto: ResistanceLoadDTO): string {
    if (dto.resistance > 9999.9 || dto.resistance < 0) return;
    return dto.resistance.toFixed(1);
  }
}
