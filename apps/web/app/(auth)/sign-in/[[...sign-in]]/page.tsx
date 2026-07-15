import { SignIn } from "@clerk/nextjs";
import { AplioLogo } from "@/components/shared/aplio-logo";

export default function SignInPage() {
  return (
    <div className="w-full max-w-md">
      <div className="flex flex-col items-center mb-10">
        <AplioLogo variant="icon" size="lg" className="mb-5" />
        <div
          className="text-[42px] tracking-[0.14em] font-extralight leading-none mb-3"
          style={{
            fontFamily: "'Outfit', 'Inter Variable', Inter, system-ui, sans-serif",
            color: "var(--text-primary)",
            textIndent: "0.14em",
          }}
        >
          Aplio
        </div>
        <div
          className="w-8 mb-3"
          style={{ height: 1.5, background: "var(--accent)" }}
        />
        <p
          className="text-sm font-editorial italic"
          style={{ color: "var(--text-muted)" }}
        >
          Your career, understood.
        </p>
      </div>

      <SignIn
        appearance={{
          elements: {
            rootBox: "mx-auto w-full",
            card: "shadow-lg",
          },
        }}
      />

      <p
        className="text-center text-xs mt-6"
        style={{ color: "var(--text-muted)" }}
      >
        By signing in, you agree to our Terms &amp; Privacy Policy.
      </p>
    </div>
  );
}
