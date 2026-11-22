/** A score as a thin ring: the arc is the score out of 100, the number sits inside. */
export function ScoreRing({ score, color, size = 64, label }: { score: number; color: string; size?: number; label?: string }) {
  const stroke = Math.max(3, Math.round(size / 16));
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  return (
    <div className="relative inline-flex shrink-0" style={{ width: size, height: size }} role="img"
         aria-label={label ?? `Score ${score} of 100`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round"
                strokeDasharray={`${c * pct} ${c}`} />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-mono font-semibold tabular-nums"
            style={{ color, fontSize: Math.round(size * 0.32) }}>
        {score}
      </span>
    </div>
  );
}
