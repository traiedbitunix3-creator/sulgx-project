import React from "react";

export default function ProgressBar({ used, total }) {
  const percent = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  let color = "#22c55e";
  if (percent > 80) color = "#ef4444";
  else if (percent > 50) color = "#f59e0b";

  return (
    <div className="progress-wrap">
      <div className="progress-track">
        <div
          className="progress-fill"
          style={{ width: `${percent}%`, background: color }}
        />
      </div>
      <div className="progress-label">
        {used.toFixed(1)} / {total.toFixed(1)} GB &nbsp;•&nbsp; {percent.toFixed(0)}٪
      </div>
    </div>
  );
}
