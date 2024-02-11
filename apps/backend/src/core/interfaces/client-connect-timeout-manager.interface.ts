export interface IClientConnectTimeoutManager {
  startTimeout(): void;

  /**
   * @returns true if the timeout was cleared, false if there was no timeout to clear
   */
  clearTimeoutIfExists(): boolean;
}
