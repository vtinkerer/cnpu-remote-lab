import { preHandlerHookHandler } from 'fastify';
import { parseAuthenticationHeader } from './parse-authentication-header';

export const validateUsernameAndPassword: preHandlerHookHandler = async (
  request,
  reply,
  done
) => {
  const { config } = request.server;
  const authHeader = request.headers.authorization;
  const authInfo = parseAuthenticationHeader(authHeader);

  if (!authInfo) {
    reply.code(401).send({ message: 'Unauthorized' });
    return;
  }
  if (
    authInfo.username !== config.lde_username ||
    authInfo.password !== config.lde_password
  ) {
    request.server.log.warn(
      `Invalid credentials provided to access ${request.url}. Username provided: ${authInfo.username} (expected: ${config.lde_username})`
    );
    if (request.url.endsWith('/test')) {
      return reply
        .code(401)
        .headers({
          'WWW-Authenticate': 'Basic realm="Login Required"',
          'Content-Type': 'application/json',
        })
        .send({
          valid: false,
          error_messages: [
            authInfo.username
              ? 'Invalid credentials: wrong username provided. Check the lab logs for further information.'
              : 'Invalid credentials: no username provided',
          ],
        });
    }

    return reply
      .code(401)
      .headers({ 'WWW-Authenticate': 'Basic realm="Login Required"' })
      .send("You don't seem to be a WebLab-Instance");
  }
};
