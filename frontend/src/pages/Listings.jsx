import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import ListingCard from "../components/ListingCard";
import { Alert, Spinner } from "../components/ui";
import { CATEGORIES, DISTRICTS } from "../config";
import { useI18n } from "../i18n";

export default function Listings() {
  const { t } = useI18n();
  const [filters, setFilters] = useState({ type: "", district: "", category: "", q: "" });
  const [listings, setListings] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams(Object.entries(filters).filter(([, v]) => v));
    api(`/listings?${params}`).then((d) => { setListings(d.listings); setError(""); }).catch((e) => setError(e.message));
  }, [filters]);

  useEffect(() => { load(); const id = setInterval(load, 15000); return () => clearInterval(id); }, [load]);
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {[["", "filter.all"], ["DISCOUNTED", "type.DISCOUNTED"], ["DONATION", "type.DONATION"]].map(([value, key]) => (
          <button key={value} onClick={() => setFilters({ ...filters, type: value })}
            className={`rounded-full px-4 py-1.5 text-sm font-semibold ${filters.type === value ? "bg-green-700 text-white" : "bg-white text-gray-700 ring-1 ring-gray-300"}`}>{t(key)}</button>
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <input className="input" placeholder={t("filter.search")} value={filters.q} onChange={set("q")} />
        <select className="input" value={filters.district} onChange={set("district")} aria-label={t("filter.district")}>
          <option value="">{t("filter.alldistricts")}</option>
          {DISTRICTS.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select className="input" value={filters.category} onChange={set("category")} aria-label={t("filter.category")}>
          <option value="">{t("filter.allcategories")}</option>
          {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <Alert>{error}</Alert>
      {!listings && !error ? <Spinner /> : listings?.length === 0 ? (
        <p className="py-12 text-center text-gray-500">{t("listing.noResults")}</p>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{listings?.map((l) => <ListingCard key={l.listingId} listing={l} />)}</div>
      )}
    </div>
  );
}
