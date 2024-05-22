import { BaseMcuSerializer, McuSerializer } from '../mcu-serializer';
import { ResetCommand } from '../rpi-only-commands/reset.command';

@McuSerializer(ResetCommand)
export class ResetSerializer extends BaseMcuSerializer {
  key = 'Reset';

  extractValue(): string {
    return '1';
  }
}
