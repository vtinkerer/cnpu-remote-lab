export interface IContextRepository {
  setIsConditionsOk(isOk: boolean): Promise<void>;
  isConditionsOk(): Promise<boolean>;
}
