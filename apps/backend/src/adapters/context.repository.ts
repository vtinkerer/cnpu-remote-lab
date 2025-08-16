import { IContextRepository } from '../core/interfaces/context-repository.interface';

export class ContextRepository implements IContextRepository {
  private isConditionsOkFlag = false;

  async setIsConditionsOk(isOk: boolean): Promise<void> {
    this.isConditionsOkFlag = isOk;
  }

  async isConditionsOk(): Promise<boolean> {
    return this.isConditionsOkFlag;
  }
}
