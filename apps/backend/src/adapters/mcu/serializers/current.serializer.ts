import { CurrentLoadDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CurrentLoadDTO)
export class CurrentSerializer extends BaseMcuSerializer {
  key = 'IL';

  extractValue(dto: CurrentLoadDTO): string {
    return dto.mA.toFixed(0);
  }
}
