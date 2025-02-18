import { ResistanceLoadDTO } from './resistance-load.dto';

import { CapacitorDTO } from './capacitor.dto';

import {
  CurrentLoadDTO,
  LoadTypeDTO,
  PWMDTO,
  PWMTypeDTO,
  VoltageInputDTO,
  VoltageOutputDto,
} from '@cnpu-remote-lab-nx/shared';

export const dtoClasses = [
  VoltageInputDTO,
  VoltageOutputDto,
  CurrentLoadDTO,
  CapacitorDTO,
  PWMDTO,
  PWMTypeDTO,
  ResistanceLoadDTO,
  LoadTypeDTO,
] as const;

export type DtoClassesType = InstanceType<(typeof dtoClasses)[number]>;
