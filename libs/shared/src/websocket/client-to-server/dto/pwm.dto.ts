import { ClientToServerDTO } from '../client-to-server.base';

export class PWM implements ClientToServerDTO {
  readonly dtoName = PWM.name;

  // Value between 0 and 100
  readonly pwmPercentage: number;

  constructor({ pwmPercentage }: { pwmPercentage: number }) {
    this.pwmPercentage = pwmPercentage;
  }

  validate() {
    return (
      (this.pwmPercentage >= 0 && this.pwmPercentage <= 100) ||
      this.pwmPercentage === 0
    );
  }
}
