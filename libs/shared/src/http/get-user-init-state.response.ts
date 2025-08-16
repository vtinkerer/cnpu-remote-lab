import { LaboratoryType } from '../laboratory-type';

export type GetUserInitStateResponse = {
  isActive: boolean;
  isConditionsOk?: boolean;
  url?: string;
  stopDate?: string;
  laboratoryType?: LaboratoryType;
};
