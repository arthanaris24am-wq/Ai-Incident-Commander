import { useEffect, useRef, useState } from "react";

import {
  FaBell,
  FaCircle,
  FaSyncAlt,
  FaServer,
} from "react-icons/fa";

import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  clearReadNotifications,
  getAIHealth,
} from "../services/api";

import NotificationPanel from "./NotificationPanel";


function TopBar({
  metrics,
  incidents,
  onRefresh,
  loading,
}) {

  const [time, setTime] = useState(
    new Date()
  );

  const [notifications, setNotifications] =
    useState([]);

  const [unreadCount, setUnreadCount] =
    useState(0);

  const [notificationOpen, setNotificationOpen] =
    useState(false);

  const [notificationLoading, setNotificationLoading] =
    useState(false);

  const [aiStatus, setAiStatus] = useState("checking"); // checking, connected, fallback

  const notificationRef = useRef(null);


  /*
   * Clock
   */
  useEffect(() => {

    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => clearInterval(timer);

  }, []);


  /*
   * Load notifications
   */
  const loadNotifications = async () => {

    try {

      setNotificationLoading(true);

      const [
        notificationData,
        unreadData,
      ] = await Promise.all([
        getNotifications(),
        getUnreadNotificationCount(),
      ]);

      setNotifications(
        Array.isArray(notificationData)
          ? notificationData
          : []
      );

      setUnreadCount(
        unreadData?.count || 0
      );

      try {
        const aiHealth = await getAIHealth();
        setAiStatus(aiHealth.status);
      } catch(err) {
        setAiStatus("fallback");
      }

    } catch (error) {

      console.error(
        "Failed to load notifications:",
        error
      );

    } finally {

      setNotificationLoading(false);

    }
  };


  /*
   * Initial notification load
   */
  useEffect(() => {

    loadNotifications();

  }, []);


  /*
   * Refresh notification count periodically
   */
  useEffect(() => {

    const timer = setInterval(() => {

      loadNotifications();

    }, 15000);

    return () => clearInterval(timer);

  }, []);


  /*
   * Close panel when clicking outside
   */
  useEffect(() => {

    const handleClickOutside = (event) => {

      if (
        notificationRef.current &&
        !notificationRef.current.contains(
          event.target
        )
      ) {

        setNotificationOpen(false);

      }

    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {

      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );

    };

  }, []);


  /*
   * Open notification panel
   */
  const handleNotificationClick = async () => {

    const newState = !notificationOpen;

    setNotificationOpen(newState);

    if (newState) {

      await loadNotifications();

    }

  };


  /*
   * Mark one notification as read
   */
  const handleMarkRead = async (id) => {

    try {

      await markNotificationAsRead(id);

      setNotifications((current) =>
        current.map((notification) =>
          notification.id === id
            ? {
                ...notification,
                is_read: true,
              }
            : notification
        )
      );

      setUnreadCount((current) =>
        Math.max(current - 1, 0)
      );

    } catch (error) {

      console.error(
        "Failed to mark notification as read:",
        error
      );

    }

  };


  /*
   * Mark all notifications as read
   */
  const handleMarkAllRead = async () => {

    try {

      await markAllNotificationsAsRead();

      setNotifications((current) =>
        current.map((notification) => ({
          ...notification,
          is_read: true,
        }))
      );

      setUnreadCount(0);

    } catch (error) {

      console.error(
        "Failed to mark all notifications as read:",
        error
      );

    }

  };


  /*
   * Clear read notifications
   */
  const handleClearRead = async () => {

    try {

      await clearReadNotifications();

      setNotifications((current) =>
        current.filter(
          (notification) =>
            !notification.is_read
        )
      );

    } catch (error) {

      console.error(
        "Failed to clear notifications:",
        error
      );

    }

  };


  const safeMetrics = metrics || {};

  const safeIncidents = Array.isArray(incidents)
    ? incidents
    : [];


  const openIncidents =
    safeIncidents.filter(
      (incident) =>
        String(incident.status).toUpperCase() !== "RESOLVED"
    ).length;


  const systemHealthy =
    (safeMetrics.cpu ?? 0) < 80 &&
    (safeMetrics.memory_percent ?? 0) < 85 &&
    (safeMetrics.disk_percent ?? 0) < 90 &&
    openIncidents === 0;


  return (

    <header className="topbar">

      <div className="topbar-left">

        <div className="page-title">

          <FaServer />

          <div>

            <h1>
              Operations Center
            </h1>

            <span>
              Real-time infrastructure monitoring
            </span>

          </div>

        </div>

      </div>


      <div className="topbar-right">

        <div
          className={
            systemHealthy
              ? "health-status healthy"
              : "health-status critical"
          }
        >

          <FaCircle />

          <div>

            <strong>
              {systemHealthy
                ? "System Healthy"
                : "Attention Required"}
            </strong>

            <small>
              {systemHealthy
                ? "All systems operational"
                : `${openIncidents} open incident(s)`}
            </small>

          </div>

        </div>


        <div className="topbar-divider"></div>

        <div
          className={
            aiStatus === "connected"
              ? "health-status healthy"
              : aiStatus === "fallback"
              ? "health-status critical"
              : "health-status"
          }
        >
          <FaCircle />
          <div>
            <strong>
              {aiStatus === "connected"
                ? "AI Online"
                : aiStatus === "fallback"
                ? "AI Fallback Mode"
                : "Checking AI..."}
            </strong>
            <small>
              {aiStatus === "connected"
                ? "Gemini RCA active"
                : "Rule-based RCA active"}
            </small>
          </div>
        </div>

        <div className="topbar-divider"></div>

        <div className="topbar-time">

          <strong>
            {time.toLocaleTimeString()}
          </strong>

          <small>
            {time.toLocaleDateString()}
          </small>

        </div>


        <button
          className={
            loading
              ? "topbar-button spinning"
              : "topbar-button"
          }
          onClick={onRefresh}
          title="Refresh dashboard"
        >

          <FaSyncAlt />

        </button>


        {/* Notification */}
        <div
          className="notification-wrapper"
          ref={notificationRef}
        >

          <button
            className={
              notificationOpen
                ? "topbar-button notification-button active"
                : "topbar-button notification-button"
            }
            onClick={handleNotificationClick}
            title="Notifications"
            aria-label="Notifications"
          >

            <FaBell />

            {unreadCount > 0 && (

              <span className="notification-badge">

                {unreadCount > 99
                  ? "99+"
                  : unreadCount}

              </span>

            )}

          </button>


          {notificationOpen && (

            <NotificationPanel
              notifications={notifications}
              unreadCount={unreadCount}
              loading={notificationLoading}
              onMarkRead={handleMarkRead}
              onMarkAllRead={handleMarkAllRead}
              onClearRead={handleClearRead}
            />

          )}

        </div>

      </div>

    </header>

  );
}


export default TopBar;