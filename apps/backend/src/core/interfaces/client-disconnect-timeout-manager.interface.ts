export interface IClientDisconnectTimeoutManager {
  startTimeout(): void;

  /**
   * @returns true if the timeout was cleared, false if there was no timeout to clear
   */
  clearTimeoutIfExists(): boolean;
}
