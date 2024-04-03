import { LoadTypeDTO, VoltageOutputDto } from '@cnpu-remote-lab-nx/shared';
import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';

@McuSerializer(LoadTypeDTO)
export class LoadTypeSerializer extends BaseMcuSerializer {
  key = 'LOAD';

  extractValue(dto: LoadTypeDTO): string {
    return dto.type.toString();
  }
}
