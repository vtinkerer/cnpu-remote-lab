import { BaseDto } from '../../dto.base';

export const isSessionIsOverDto = (dto: unknown): dto is SessionIsOver =>
  (dto as any).dtoName && (dto as any).dtoName === SessionIsOver.name;

export class SessionIsOver implements BaseDto {
  dtoName = SessionIsOver.name;

  backUrl: string;

  constructor({ backUrl }: { backUrl: string }) {
    this.backUrl = backUrl;
  }
}
