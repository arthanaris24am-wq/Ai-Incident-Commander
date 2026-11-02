import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

function LiveChart({ title, data, dataKey, color }) {
  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: "12px",
        padding: "20px",
        marginTop: "25px",
        boxShadow: "0 0 10px rgba(0,0,0,.3)",
      }}
    >
      <h3 style={{ marginBottom: "20px" }}>{title}</h3>

      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid stroke="#374151" />

          <XAxis dataKey="time" />

          <YAxis domain={[0, 100]} />

          <Tooltip />

          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            strokeWidth={3}
            dot={false}
            isAnimationActive={true}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default LiveChart;