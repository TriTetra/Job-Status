import { getBriefing } from "@/features/briefing/api";
import { BriefingHeader } from "./_components/briefing-header";
import { BriefingHeadline } from "./_components/briefing-headline";
import { BriefingChanges } from "./_components/briefing-changes";
import { BriefingTodos } from "./_components/briefing-todos";
import { BriefingWeek } from "./_components/briefing-week";
import { BriefingClosing } from "./_components/briefing-closing";

/**
 * The daily briefing: what changed since your last visit, the one job worth your
 * attention, what to do next, and the week in three numbers.
 */
export default async function BriefingPage() {
  const b = await getBriefing();
  return (
    <div className="max-w-[880px] mx-auto px-6 lg:px-10 py-14">
      <BriefingHeader dateline={b.dateline} greeting={b.greeting} lead={b.lead} />
      {b.headline && <BriefingHeadline h={b.headline} />}
      <BriefingChanges lines={b.changes} />
      <BriefingTodos todos={b.todos} />
      <BriefingWeek numbers={b.week} />
      <BriefingClosing lines={b.closing} />
    </div>
  );
}
