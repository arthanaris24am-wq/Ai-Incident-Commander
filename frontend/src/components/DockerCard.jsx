import {
  FaPlay,
  FaStop,
  FaRedo,
  FaDocker,
} from "react-icons/fa";

function DockerCard({
  container,
  onStart,
  onStop,
  onRestart,
  onLogs,
}) {
  return (
    <div className="docker-card">

      <div className="docker-header">

        <FaDocker size={28} />

        <div>

          <h3>{container.name}</h3>

          <p>{container.image[0]}</p>

        </div>

      </div>

      <div className="docker-status">

        <span
          className={
            container.status === "running"
              ? "badge-running"
              : "badge-stopped"
          }
        >
          {container.status}
        </span>

      </div>

      <div className="docker-buttons">

        <button
          className="btn-green"
          onClick={() => onStart(container.id)}
        >
          <FaPlay /> Start
        </button>

        <button
          className="btn-red"
          onClick={() => onStop(container.id)}
        >
          <FaStop /> Stop
        </button>

        <button
          className="btn-orange"
          onClick={() => onRestart(container.id)}
        >
          <FaRedo /> Restart
        </button>

        <button
          className="btn-blue"
          onClick={() => onLogs(container.id)}
        >
          Logs
        </button>

      </div>

    </div>
  );
}

export default DockerCard;