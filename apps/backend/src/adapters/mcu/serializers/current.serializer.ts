import { CurrentLoadDTO } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(CurrentLoadDTO)
export class CurrentSerializer extends BaseMcuSerializer {
  key = 'IL';

  extractValue(dto: CurrentLoadDTO): string {
    if (dto.mA > 10_000 || dto.mA < 0) return;
    return (dto.mA / 1000).toFixed(2);
  }
}
