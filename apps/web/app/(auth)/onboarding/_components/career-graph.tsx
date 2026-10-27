"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import type { CareerGraphData, CareerGraphEdge as GraphEdge, CareerGraphNode as GraphNode } from "@/features/onboarding/types";

interface CareerGraphProps { data: CareerGraphData; }

export function CareerGraph({ data }: CareerGraphProps) {
  const [visibleNodes, setVisibleNodes] = useState<string[]>([]);
  const [visibleEdges, setVisibleEdges] = useState<string[]>([]);

  const allNodes = useMemo<GraphNode[]>(
    () => [{ id: "you", type: "you", label: "You", confidence: 1, metadata: {} }, ...data.nodes],
    [data.nodes],
  );

  // You → every skill, plus the existing project/company → skill edges
  const allEdges = useMemo<GraphEdge[]>(
    () => [
      ...data.nodes.filter((n) => n.type === "skill").map((n) => ({ source: "you", target: n.id, weight: 1 })),
      ...data.edges,
    ],
    [data.nodes, data.edges],
  );

  useEffect(() => {
    const t = setInterval(() => {
      setVisibleNodes((prev) => {
        if (prev.length >= allNodes.length) { clearInterval(t); return prev; }
        return [...prev, allNodes[prev.length].id];
      });
    }, 160);
    return () => clearInterval(t);
  }, [allNodes]);

  useEffect(() => {
    if (visibleNodes.length >= allNodes.length) {
      const t = setInterval(() => {
        setVisibleEdges((prev) => {
          if (prev.length >= allEdges.length) { clearInterval(t); return prev; }
          const e = allEdges[prev.length];
          return [...prev, `${e.source}-${e.target}`];
        });
      }, 70);
      return () => clearInterval(t);
    }
  }, [visibleNodes.length, allEdges, allNodes.length]);

  // Layout: You merkez · skill iç halka · project/company dış halka
  const cx = 200, cy = 150;
  const skills = data.nodes.filter((n) => n.type === "skill");
  const others = data.nodes.filter((n) => n.type !== "skill");

  const pos = (id: string) => {
    if (id === "you") return { x: cx, y: cy };
    const node = allNodes.find((n) => n.id === id);
    if (!node) return { x: cx, y: cy };
    if (node.type === "skill") {
      const i = skills.findIndex((s) => s.id === id);
      const a = (i / Math.max(skills.length, 1)) * 2 * Math.PI - Math.PI / 2;
      return { x: cx + 78 * Math.cos(a), y: cy + 78 * Math.sin(a) };
    }
    const i = others.findIndex((o) => o.id === id);
    const a = (i / Math.max(others.length, 1)) * 2 * Math.PI - Math.PI / 2;
    return { x: cx + 135 * Math.cos(a), y: cy + 135 * Math.sin(a) };
  };

  const radius = (n: GraphNode) =>
    n.type === "you" ? 13 : n.type === "skill" ? 5 + n.confidence * 6 : n.type === "achievement" ? 7 : 5;

  const color = (t: string) =>
    t === "you" ? "var(--text-primary)"
    : t === "skill" ? "var(--accent)"
    : t === "achievement" ? "var(--warning, #e6a817)"
    : t === "project" ? "var(--success)"
    : "var(--info, #6BA5D7)";

  return (
    <svg viewBox="0 0 400 300" className="w-full h-auto">
      {allEdges.map((e) => {
        const s = pos(e.source), t = pos(e.target);
        const eid = `${e.source}-${e.target}`;
        const vis = visibleEdges.includes(eid);
        return (
          <motion.line key={eid} x1={s.x} y1={s.y} x2={t.x} y2={t.y}
            stroke="var(--border)" strokeWidth={1}
            initial={{ pathLength: 0, opacity: 0 }}
            animate={vis ? { pathLength: 1, opacity: 0.35 } : {}}
            transition={{ duration: 0.4, ease: "easeOut" }} />
        );
      })}

      {allNodes.map((node) => {
        const p = pos(node.id);
        const vis = visibleNodes.includes(node.id);
        const r = radius(node);
        return (
          <motion.g key={node.id}
            initial={{ scale: 0, opacity: 0 }}
            animate={vis ? { scale: 1, opacity: 1 } : {}}
            transition={{ duration: 0.3, ease: "easeOut" }}>
            {node.type === "you" && (
              <motion.circle cx={p.x} cy={p.y} r={r} fill="none" stroke="var(--accent)" strokeWidth={1.5}
                animate={{ r: [r, r + 9, r], opacity: [0.5, 0, 0.5] }}
                transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }} />
            )}
            {node.type === "achievement" && (
              <motion.circle
                cx={p.x} cy={p.y} r={r} fill="none"
                stroke="var(--warning, #e6a817)" strokeWidth={1}
                animate={{ r: [r, r + 6, r], opacity: [0.45, 0, 0.45] }}
                transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut", delay: 0.4 }}
              />
            )}
            <circle cx={p.x} cy={p.y} r={r} fill={color(node.type)} />
            {(node.type === "you" || node.type === "skill" || node.type === "achievement") && (
              <text x={p.x} y={p.y + r + 10} textAnchor="middle" style={{ fontSize: "8.5px" }} className="fill-current text-[var(--text-secondary)]">
                {node.label}
              </text>
            )}
          </motion.g>
        );
      })}
    </svg>
  );
}
