import { getBriefing } from "@/features/briefing/api";
import { BriefingGreeting } from "./_components/briefing-greeting";
import { BriefingFocus } from "./_components/briefing-focus";
import { BriefingOpportunities } from "./_components/briefing-opportunities";
import { BriefingEvidenceProgress } from "./_components/briefing-evidence-progress";
import { BriefingClosing } from "./_components/briefing-closing";
import { BriefingEmpty } from "./_components/briefing-empty";

export default async function BriefingPage() {
  const result = await getBriefing();

  if (result.status === "empty") {
    return <BriefingEmpty watching={result.data.watching} stats={result.data.stats} greeting={result.data.greeting} />;
  }

  const { greeting, brief, focus, opportunities, evidence, progress, closing } = result.data;

  return (
    <div className="max-w-[1000px] mx-auto px-6 lg:px-8 py-14">
      <BriefingGreeting
        name={greeting.name}
        greeting={greeting.greeting}
        subtitle={greeting.subtitle}
        brief={brief}
      />
      <BriefingFocus items={focus} />
      <BriefingOpportunities opportunities={opportunities} />
      <BriefingEvidenceProgress evidence={evidence} progress={progress} />
      <BriefingClosing lines={closing.lines} />
    </div>
  );
}
