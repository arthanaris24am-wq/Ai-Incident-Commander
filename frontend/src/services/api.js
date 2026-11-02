const BASE_URL = "http://127.0.0.1:5000/api";

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}

// Metrics
export const getMetrics = () =>
  fetchJSON(`${BASE_URL}/metrics/`);

// Incidents
export const getIncidents = () =>
  fetchJSON(`${BASE_URL}/incidents/`);

export const getIncidentDetails = (id) =>
  fetchJSON(`${BASE_URL}/incidents/${id}`);

export const investigateIncident = (id) =>
  fetchJSON(`${BASE_URL}/incidents/${id}/investigate`, { method: "POST" });

export const approveAction = (incident_id, action_id) =>
  fetchJSON(`${BASE_URL}/incidents/${incident_id}/actions/${action_id}/approve`, { method: "POST" });

export const executeAction = (incident_id, action_id) =>
  fetchJSON(`${BASE_URL}/incidents/${incident_id}/actions/${action_id}/execute`, { method: "POST" });

export const resolveIncident = (id) =>
  fetchJSON(`${BASE_URL}/incidents/${id}/resolve`, { method: "POST" });

export const resolveAllIncidents = () =>
  fetchJSON(`${BASE_URL}/incidents/resolve-all`, { method: "POST" });

// Logs
export const getApplicationLogs = (lines = 200) =>
  fetchJSON(`${BASE_URL}/logs/application?lines=${lines}`);

export const getLogEvents = (limit = 100) =>
  fetchJSON(`${BASE_URL}/logs/events?limit=${limit}`);

export const injectTestLog = (level, message, component = "application") =>
  fetchJSON(`${BASE_URL}/logs/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level, message, component }),
  });

export const clearApplicationLogs = () =>
  fetchJSON(`${BASE_URL}/logs/clear`, { method: "POST" });

// Docker
export const getContainers = () =>
  fetchJSON(`${BASE_URL}/docker/containers`);

export const getContainerLogs = (id) =>
  fetchJSON(`${BASE_URL}/docker/logs/${id}`);

export const startContainer = (id) =>
  fetchJSON(`${BASE_URL}/docker/start/${id}`, {
    method: "POST",
  });

export const stopContainer = (id) =>
  fetchJSON(`${BASE_URL}/docker/stop/${id}`, {
    method: "POST",
  });

export const restartContainer = (id) =>
  fetchJSON(`${BASE_URL}/docker/restart/${id}`, {
    method: "POST",
  });

// AI
export const getAIReport = () =>
  fetchJSON(`${BASE_URL}/ai/report`);

export const getAIHealth = () =>
  fetchJSON(`${BASE_URL}/ai/health`);

// Notifications

export const getNotifications = () =>
  fetchJSON(`${BASE_URL}/notifications/`);

export const getUnreadNotificationCount = () =>
  fetchJSON(`${BASE_URL}/notifications/unread-count`);

export const markNotificationAsRead = (id) =>
  fetchJSON(`${BASE_URL}/notifications/${id}/read`, {
    method: "PATCH",
  });

export const markAllNotificationsAsRead = () =>
  fetchJSON(`${BASE_URL}/notifications/read-all`, {
    method: "PATCH",
  });

export const deleteNotification = (id) =>
  fetchJSON(`${BASE_URL}/notifications/${id}`, {
    method: "DELETE",
  });

export const clearReadNotifications = () =>
  fetchJSON(`${BASE_URL}/notifications/clear-read`, {
    method: "DELETE",
  });