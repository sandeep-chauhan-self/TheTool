export const cancelJob = async (jobId) => {
  const response = await api.post(`/cancel-job/${jobId}`);
  return response.data;
};

export default api;
