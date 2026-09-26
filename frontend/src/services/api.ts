import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const submitTask = async (prompt: string) => {
    const response = await axios.post(`${API_BASE}/tasks`, { prompt });
    return response.data;
};

export const getAgents = async () => {
    const response = await axios.get(`${API_BASE}/agents`);
    return response.data;
};

export const getStatistics = async () => {
    const response = await axios.get(`${API_BASE}/dashboard/statistics`);
    return response.data;
};

export const getRecentExecutions = async () => {
    const response = await axios.get(`${API_BASE}/dashboard/recent-executions`);
    return response.data;
};
