export interface Company {
  name: string;
  tier: string;
  industry: string | null;
  headquarters: string | null;
  tech_stack: string[];
  hiring_trend: string;
  open_positions_count: number;
}
