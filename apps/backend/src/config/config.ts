import { Static, Type } from '@sinclair/typebox';

export const configSchema = Type.Object({
  username: Type.String(),
  password: Type.String(),
  frontend_url: Type.String(),
  weblab_poll_interval_seconds: Type.Number(),
  weblab_timeout_seconds: Type.Number(),
  weblab_expired_users_timeout_seconds: Type.Number(),
  client_connect_timeout_seconds: Type.Number(),
  client_disconnect_timeout_seconds: Type.Number(),
  scope_script_path: Type.String(),
  scope_script_delimiter: Type.String(),
  baud_rate: Type.Number(),
  serial_port_file_path: Type.String(),
});

export type ConfigType = Static<typeof configSchema>;
