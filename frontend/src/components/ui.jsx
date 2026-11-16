import { CATEGORY_EMOJI, IMAGE_BASE_URL } from "../config";
import { humanize, useCountdown } from "../format";
import { useI18n } from "../i18n";

export const Spinner = ({ label = "Loading…" }) => <p className="py-10 text-center text-gray-500">{label}</p>;

export function Alert({ kind = "error", children }) {
  if (!children) return null;
  const color = kind === "error" ? "border-red-200 bg-red-50 text-red-800" : kind === "success" ? "border-green-200 bg-green-50 text-green-800" : "border-amber-200 bg-amber-50 text-amber-900";
  return <div role="alert" className={`rounded-lg border px-4 py-3 text-sm ${color}`}>{children}</div>;
}

export function Field({ label, children, hint }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-gray-500">{hint}</span>}
    </label>
  );
}

export function TypeBadge({ listing }) {
  const { t } = useI18n();
  const donation = listing.listingType === "DONATION";
  const cls = donation ? "bg-purple-100 text-purple-800" : "bg-amber-100 text-amber-900";
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${cls}`}>{t(`type.${listing.listingType}`)}</span>;
}

export function Countdown({ to, prefix }) {
  const { t } = useI18n();
  const text = humanize(useCountdown(to));
  return (
    <span className={text ? "text-gray-700" : "text-red-600"}>
      {prefix && `${prefix}: `}<strong>{text || t("listing.closed")}</strong>
    </span>
  );
}

export function FoodImage({ listing, className = "" }) {
  if (listing.imageKey && IMAGE_BASE_URL) {
    return <img src={`${IMAGE_BASE_URL}/${listing.imageKey}`} alt={listing.productName} loading="lazy" className={`object-cover ${className}`} />;
  }
  return <div className={`flex items-center justify-center bg-green-50 text-5xl ${className}`} aria-hidden>{CATEGORY_EMOJI[listing.category] || "🍽️"}</div>;
}

export const waLink = (number, text) => `https://wa.me/${number}?text=${encodeURIComponent(text)}`;
