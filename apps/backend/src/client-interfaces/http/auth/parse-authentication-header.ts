export function parseAuthenticationHeader(header?: string): {
  username: string;
  password: string;
} | null {
  if (!header) return null;

  const b64 = header.split(' ')[1];
  if (!b64) return null;

  const [username, password] = atob(b64).split(':');
  return { username, password };
}
