"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface GraphNode {
  id: string;
  type: string;
  label: string;
  confidence: number;
  metadata: any;
}

interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

interface CareerGraphProps {
  data: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    stats: any;
  };
}

export function CareerGraph({ data }: CareerGraphProps) {
  const [visibleNodes, setVisibleNodes] = useState<string[]>([]);
  const [visibleEdges, setVisibleEdges] = useState<string[]>([]);

  // Animate nodes appearing sequentially
  useEffect(() => {
    const nodeInterval = setInterval(() => {
      setVisibleNodes((prev) => {
        if (prev.length >= data.nodes.length) {
          clearInterval(nodeInterval);
          return prev;
        }
        return [...prev, data.nodes[prev.length].id];
      });
    }, 200);

    return () => clearInterval(nodeInterval);
  }, [data.nodes]);

  // Animate edges after nodes
  useEffect(() => {
    if (visibleNodes.length === data.nodes.length) {
      const edgeInterval = setInterval(() => {
        setVisibleEdges((prev) => {
          if (prev.length >= data.edges.length) {
            clearInterval(edgeInterval);
            return prev;
          }
          const edge = data.edges[prev.length];
          return [...prev, `${edge.source}-${edge.target}`];
        });
      }, 100);

      return () => clearInterval(edgeInterval);
    }
  }, [visibleNodes, data.edges, data.nodes.length]);

  // Simple force-directed layout (circular for now)
  const centerX = 300;
  const centerY = 200;
  const radius = 120;

  const getNodePosition = (index: number) => {
    const angle = (index / data.nodes.length) * 2 * Math.PI;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case "skill":
        return "var(--accent)"; // accent
      case "project":
        return "var(--success)"; // success
      case "company":
        return "var(--info)"; // info
      default:
        return "var(--text-muted)"; // muted
    }
  };

  return (
    <svg viewBox="0 0 600 400" className="w-full h-auto">
      {/* Edges */}
      {data.edges.map((edge, i) => {
        const sourceIndex = data.nodes.findIndex((n) => n.id === edge.source);
        const targetIndex = data.nodes.findIndex((n) => n.id === edge.target);
        if (sourceIndex === -1 || targetIndex === -1) return null;

        const sourcePos = getNodePosition(sourceIndex);
        const targetPos = getNodePosition(targetIndex);
        const edgeId = `${edge.source}-${edge.target}`;
        const isVisible = visibleEdges.includes(edgeId);

        return (
          <motion.line
            key={edgeId}
            x1={sourcePos.x}
            y1={sourcePos.y}
            x2={targetPos.x}
            y2={targetPos.y}
            stroke="var(--border)"
            strokeWidth={1}
            initial={{ pathLength: 0, opacity: 0 }}
            animate={isVisible ? { pathLength: 1, opacity: 0.3 } : {}}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        );
      })}

      {/* Nodes */}
      {data.nodes.map((node, i) => {
        const pos = getNodePosition(i);
        const isVisible = visibleNodes.includes(node.id);
        const nodeRadius = node.type === "skill" ? 8 : 6;

        return (
          <motion.g
            key={node.id}
            initial={{ scale: 0, opacity: 0 }}
            animate={isVisible ? { scale: 1, opacity: 1 } : {}}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <circle
              cx={pos.x}
              cy={pos.y}
              r={nodeRadius}
              fill={getNodeColor(node.type)}
            />
            <text
              x={pos.x}
              y={pos.y + nodeRadius + 12}
              textAnchor="middle"
              className="text-xs fill-current text-[var(--text-secondary)]"
              style={{ fontSize: "10px" }}
            >
              {node.label}
            </text>
          </motion.g>
        );
      })}
    </svg>
  );
}
