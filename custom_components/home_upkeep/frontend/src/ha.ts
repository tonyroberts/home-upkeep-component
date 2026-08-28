/** Minimal HA frontend types for what this panel actually uses. */

export type UnsubscribeFunc = () => void;

export interface Connection {
  sendMessagePromise<T>(message: Record<string, unknown>): Promise<T>;
  subscribeMessage<T>(
    callback: (result: T) => void,
    subscribeMessage: Record<string, unknown>,
  ): Promise<UnsubscribeFunc>;
}

export interface HomeAssistant {
  connection: Connection;
  states: Record<string, unknown>;
}
