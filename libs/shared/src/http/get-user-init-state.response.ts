import { LaboratoryType } from '../laboratory-type';

export type GetUserInitStateResponse = {
  isActive: boolean;
  url?: string;
  stopDate?: string;
  laboratoryType?: LaboratoryType;
};
