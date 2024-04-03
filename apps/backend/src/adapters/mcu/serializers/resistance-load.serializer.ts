import { ResistanceLoadDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(ResistanceLoadDTO)
export class ResistanceLoadSerializer extends BaseMcuSerializer {
  key = 'RL';

  extractValue(dto: ResistanceLoadDTO): string {
    return dto.resistance.toString();
  }
}
