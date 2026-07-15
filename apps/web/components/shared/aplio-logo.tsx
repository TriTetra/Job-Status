import Image from "next/image";
import { cn } from "@/lib/utils";

interface AplioLogoProps {
  variant?: "wordmark" | "icon";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const iconPx = { sm: 24, md: 32, lg: 48 } as const;

export function AplioLogo({ variant = "wordmark", size = "md", className }: AplioLogoProps) {
  const px = iconPx[size];

  if (variant === "icon") {
    return (
      <Image
        src="/logo-white.png"
        alt="Aplio"
        width={px}
        height={px}
        className={cn("shrink-0", className)}
        priority
      />
    );
  }

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Image
        src="/logo-white.png"
        alt="Aplio"
        width={px}
        height={px}
        className="shrink-0"
        priority
      />
      <span
        className="font-semibold tracking-tight leading-none"
        style={{ fontSize: px * 0.6, color: "var(--text-primary)" }}
      >
        Aplio
      </span>
    </div>
  );
}
