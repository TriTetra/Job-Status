import { apiFetch } from "@/lib/api/client";

/** GET /api/jobs/posting — the full posting as clean text blocks + what was read from it. */
export interface PostingBlock {
  type: "h" | "p" | "li";
  text: string;
}

export interface Posting {
  url: string;
  company: string;
  company_key: string | null;
  title: string;
  location: string;
  department: string | null;
  employment_type: string | null;
  posted_at: string | null;
  closed: boolean;
  application_url: string;
  /** Found through a job feed: credited, with a link back to the feed's page */
  via: { name: string; url: string } | null;
  facts: {
    summary: string | null;
    seniority: string | null;
    min_years: number | null;
    workplace: string | null;
    remote_regions: string[];
    visa: "yes" | "no" | null;
    salary: { min: number | null; max: number | null; currency: string; period: string } | null;
    required_skills: string[];
    nice_to_have: string[];
    read_by: "claude" | "keywords";
  };
  blocks: PostingBlock[];
}

export const getPosting = (url: string) => apiFetch<Posting>(`/api/jobs/posting?url=${encodeURIComponent(url)}`);
