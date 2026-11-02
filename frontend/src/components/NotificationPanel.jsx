import {
  FaCheck,
  FaCheckDouble,
  FaTrash,
  FaExclamationCircle,
  FaExclamationTriangle,
} from "react-icons/fa";


function getSeverityIcon(severity) {
  if (severity === "CRITICAL") {
    return <FaExclamationCircle />;
  }

  if (severity === "HIGH") {
    return <FaExclamationTriangle />;
  }

  return <FaExclamationTriangle />;
}


function formatTime(timestamp) {
  if (!timestamp) {
    return "";
  }

  const date = new Date(
    timestamp.replace(" ", "T") + "Z"
  );

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  const now = new Date();

  const diffSeconds = Math.floor(
    (now.getTime() - date.getTime()) / 1000
  );

  if (diffSeconds < 60) {
    return "Just now";
  }

  const diffMinutes = Math.floor(
    diffSeconds / 60
  );

  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.floor(
    diffMinutes / 60
  );

  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.floor(
    diffHours / 24
  );

  return `${diffDays}d ago`;
}


function NotificationPanel({
  notifications,
  unreadCount,
  loading,
  onMarkRead,
  onMarkAllRead,
  onClearRead,
}) {

  return (
    <div className="notification-panel">

      <div className="notification-panel-header">

        <div>
          <h3>Notifications</h3>

          <span>
            {unreadCount > 0
              ? `${unreadCount} unread`
              : "All caught up"}
          </span>
        </div>

        <div className="notification-header-actions">

          {unreadCount > 0 && (
            <button
              className="notification-action-button"
              onClick={onMarkAllRead}
              title="Mark all as read"
            >
              <FaCheckDouble />
            </button>
          )}

          <button
            className="notification-action-button"
            onClick={onClearRead}
            title="Clear read notifications"
          >
            <FaTrash />
          </button>

        </div>

      </div>


      <div className="notification-panel-body">

        {loading ? (

          <div className="notification-empty">
            Loading notifications...
          </div>

        ) : notifications.length === 0 ? (

          <div className="notification-empty">

            <FaCheck />

            <span>
              No notifications
            </span>

            <small>
              You're all caught up.
            </small>

          </div>

        ) : (

          notifications.map((notification) => (

            <div
              key={notification.id}
              className={
                notification.is_read
                  ? "notification-item read"
                  : "notification-item unread"
              }
            >

              <div
                className={`notification-severity ${notification.severity.toLowerCase()}`}
              >
                {getSeverityIcon(
                  notification.severity
                )}
              </div>


              <div className="notification-content">

                <div className="notification-item-top">

                  <span
                    className={`notification-severity-label ${notification.severity.toLowerCase()}`}
                  >
                    {notification.severity}
                  </span>

                  <span className="notification-time">
                    {formatTime(
                      notification.created_at
                    )}
                  </span>

                </div>


                <strong>
                  {notification.title}
                </strong>


                <p>
                  {notification.message}
                </p>


                <div className="notification-item-bottom">

                  <small>
                    {notification.source}
                  </small>

                  {!notification.is_read && (

                    <button
                      className="notification-read-button"
                      onClick={() =>
                        onMarkRead(
                          notification.id
                        )
                      }
                    >
                      <FaCheck />

                      Mark as read
                    </button>

                  )}

                </div>

              </div>

            </div>

          ))

        )}

      </div>


      {notifications.length > 0 && (
        <div className="notification-panel-footer">

          <span>
            {notifications.length} notification
            {notifications.length !== 1
              ? "s"
              : ""}
          </span>

        </div>
      )}

    </div>
  );
}


export default NotificationPanel;