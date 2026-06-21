// src/modules/Auth/api.js
import client from '../../api/client';

export const authApi = {
  // درخواست دریافت کد لاگین
  requestCode: (data) => client.post('/auth/request-code', data),
  
  // درخواست تایید کد
  verifyCode: (data) => client.post('/auth/verify-code', data),
};