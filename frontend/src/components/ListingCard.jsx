import { Link } from "react-router-dom";
import { lkr } from "../format";
import { useI18n } from "../i18n";
import { Countdown, FoodImage, TypeBadge } from "./ui";

export default function ListingCard({ listing }) {
  const { t } = useI18n();
  const free = listing.listingType === "DONATION";
  const pct = !free && listing.originalPrice ? Math.round((1 - listing.discountedPrice / listing.originalPrice) * 100) : 0;
  return (
    <Link to={`/listings/${listing.listingId}`} className="card block overflow-hidden transition hover:shadow-md">
      <div className="relative">
        <FoodImage listing={listing} className="h-40 w-full" />
        {pct > 0 && <span className="absolute right-2 top-2 rounded-full bg-red-600 px-2 py-0.5 text-xs font-bold text-white">-{pct}%</span>}
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <TypeBadge listing={listing} />
          {listing.convertedFromDiscount && <span className="text-xs text-purple-700">♻︎</span>}
        </div>
        <h3 className="text-lg font-semibold leading-tight">{listing.productName}</h3>
        <p className="text-sm text-gray-600">{listing.orgName} · {listing.orgDistrict}</p>
        <div className="flex items-baseline gap-2">
          {free ? <span className="text-lg font-bold text-purple-700">{t("listing.free")}</span> : (
            <>
              <span className="text-lg font-bold text-green-800">{lkr(listing.discountedPrice)}</span>
              <span className="text-sm text-gray-400 line-through">{lkr(listing.originalPrice)}</span>
            </>
          )}
          <span className="ml-auto text-sm text-gray-600">{listing.availableQuantity} {t("listing.left")}</span>
        </div>
        <p className="text-xs"><Countdown to={listing.reserveBy} prefix={t("listing.reserveBy")} /></p>
      </div>
    </Link>
  );
}
