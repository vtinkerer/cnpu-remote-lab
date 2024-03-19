import type { GetUserInitStateResponse } from '@cnpu-remote-lab-nx/shared';
import { appAxios } from './axios';

export const getInitState = async (sessionId: string) => {
  const res = await appAxios.get<GetUserInitStateResponse>(`/sessions/init-state/${sessionId}`, {
    headers: {
      'Cache-Control': 'no-cache',
      Pragma: 'no-cache',
      Expires: '0',
    },
  });
  return res.data;
};
