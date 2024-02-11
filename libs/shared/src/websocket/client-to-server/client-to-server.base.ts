import { BaseDto } from '../dto.base';

export abstract class ClientToServerDTO extends BaseDto {
  abstract validate(): boolean;
}
