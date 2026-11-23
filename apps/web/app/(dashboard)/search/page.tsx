import { Suspense } from "react";
import { SearchView } from "./_components/search-view";

export default function SearchPage() {
  // The query lives in the URL (useSearchParams needs a Suspense boundary)
  return (
    <Suspense>
      <SearchView />
    </Suspense>
  );
}
