import { DateTime } from 'luxon';

export abstract class WebLabUser {
  abstract isActive(): boolean;
  abstract isAnonymous(): boolean;
}

export class AnonymousUser extends WebLabUser {
  isActive() {
    return false;
  }

  isAnonymous() {
    return true;
  }
}

export abstract class CurrentOrExpiredUser extends WebLabUser {
  sessionId: string;
  back: string;
  lastPoll: DateTime;
  maxDate: DateTime;
  startDate: DateTime;
  username: string;
  usernameUnique: string;
  exited: boolean;
  data: unknown;
  locale?: string;
  fullName?: string;
  experimentName: string;
  categoryName?: string;
  experimentId: string;
  requestClientData: Record<string, any>;
  requestServerData: Record<string, any>;

  constructor(user: IUser) {
    super();
    this.sessionId = user.sessionId;
    this.back = user.back;
    this.lastPoll = user.lastPoll;
    this.maxDate = user.maxDate;
    this.startDate = user.startDate;
    this.username = user.username;
    this.usernameUnique = user.usernameUnique;
    this.exited = user.exited;
    this.data = user.data;
    this.locale = user.locale;
    this.fullName = user.fullName;
    this.experimentName = user.experimentName;
    this.categoryName = user.categoryName;
    this.experimentId = user.experimentId;
    this.requestClientData = user.requestClientData;
    this.requestServerData = user.requestServerData;
  }
}
export interface IUser {
  sessionId: string;
  back: string;
  lastPoll: DateTime;
  maxDate: DateTime;
  startDate: DateTime;
  username: string;
  usernameUnique: string;
  exited: boolean;
  data: unknown;
  locale?: string;
  fullName?: string;
  experimentName: string;
  categoryName?: string;
  experimentId: string;
  requestClientData: Record<string, any>;
  requestServerData: Record<string, any>;
}

export class CurrentUser extends CurrentOrExpiredUser {
  isActive(): boolean {
    return !this.exited;
  }

  isAnonymous(): boolean {
    return false;
  }

  constructor(user: IUser) {
    super(user);
  }

  timeLeft() {
    return Math.max(this.maxDate.diffNow('seconds').seconds, 0);
  }

  timeWithoutPolling() {
    return DateTime.now().diff(this.lastPoll).seconds, 0;
  }

  expirationDate() {
    return this.startDate.plus({ seconds: 30 }).plus({
      seconds: this.maxDate.diff(this.startDate).seconds,
    });
  }

  toExpiredUser() {
    return new ExpiredUser({ ...this, isDisposingResources: true });
  }
}

export class ExpiredUser extends CurrentOrExpiredUser {
  isDisposingResources: boolean;

  isActive(): boolean {
    return false;
  }

  isAnonymous(): boolean {
    return false;
  }

  constructor(user: IUser & { isDisposingResources: boolean }) {
    super(user);
    this.isDisposingResources = user.isDisposingResources;
  }
}
