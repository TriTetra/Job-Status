"use client";

import { cn } from "@/lib/utils";
import { type ReactNode } from "react";

interface FadeInSectionProps {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "article";
}

export function FadeInSection({
  children,
  delay = 0,
  className,
  as: Component = "div",
}: FadeInSectionProps) {
  return (
    <Component
      className={cn("animate-fade-in-up", className)}
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}
    >
      {children}
    </Component>
  );
}
