import axios from 'axios';

// In production (served by Nginx or similar), /api is proxied to the backend.
// In local dev, Vite proxies /api to http://localhost:8000.
// So we can just use /api as the base URL.

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getPumps = async () => {
  const response = await api.get('/pumps/');
  return response.data;
};

export const getPump = async (id: number) => {
  const response = await api.get(`/pumps/${id}`);
  return response.data;
};

export const createPump = async (data: any) => {
  const response = await api.post('/pumps/', data);
  return response.data;
};

export const updatePump = async (id: number, data: any) => {
  const response = await api.patch(`/pumps/${id}`, data);
  return response.data;
};

export const deletePump = async (id: number) => {
  const response = await api.delete(`/pumps/${id}`);
  return response.data;
};

export const createCurveSet = async (data: any) => {
  const response = await api.post('/curve-sets/', data);
  return response.data;
};

export const getCurveSet = async (id: number) => {
  const response = await api.get(`/curve-sets/${id}`);
  return response.data;
};

export const updateCurveSet = async (id: number, data: any) => {
  const response = await api.patch(`/curve-sets/${id}`, data);
  return response.data;
};

export const deleteCurveSet = async (id: number) => {
  const response = await api.delete(`/curve-sets/${id}`);
  return response.data;
};

export const addCurveSeries = async (curveSetId: number, data: any) => {
    const response = await api.post(`/curve-sets/${curveSetId}/series`, data);
    return response.data;
};

export const deleteCurveSeries = async (seriesId: number) => {
    const response = await api.delete(`/curve-sets/series/${seriesId}`);
    return response.data;
};

export const validateCurvePoints = async (data: any) => {
    const response = await api.post(`/curve-sets/validate`, data);
    return response.data;
};

export const evaluateSeries = async (seriesId: number, flow: number, head: number | null) => {
    const response = await api.post(`/curve-sets/series/${seriesId}/evaluate`, { flow, head_optional: head });
    return response.data;
};
