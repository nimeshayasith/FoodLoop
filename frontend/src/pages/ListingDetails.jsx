import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { Alert, Countdown, Field, FoodImage, Spinner, TypeBadge, waLink } from "../components/ui";
import { formatDateTime, lkr } from "../format";
import { useI18n } from "../i18n";

export default function ListingDetails() {
  const { id } = useParams();
  const { t } = useI18n();
  const { user, profile } = useAuth();
  const navigate = useNavigate();
  const [listing, setListing] = useState(null);
  const [qty, setQty] = useState(1);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    api(`/listings/${id}`).then((d) => setListing(d.listing)).catch((e) => setError(e.message));
  }, [id]);
  useEffect(() => { load(); const timer = setInterval(load, 10000); return () => clearInterval(timer); }, [load]);

  if (error && !listing) return <Alert>{error}</Alert>;
  if (!listing) return <Spinner />;

  const free = listing.listingType === "DONATION";
  const max = Math.max(1, Math.min(listing.maxPerCustomer, listing.availableQuantity));
  const canReserve = profile && profile.role !== "BUSINESS" && (!free || profile.role === "CHARITY");

  async function reserve() {
    setBusy(true); setError("");
    try {
      await api(`/listings/${id}/reserve`, { method: "POST", body: { quantity: Number(qty) }, auth: true });
      navigate("/reservations");
    } catch (e) {
      setError(e.message); load();
    } finally { setBusy(false); }
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <FoodImage listing={listing} className="h-72 w-full rounded-xl md:h-full" />
      <div className="space-y-4">
        <div className="flex items-center gap-2"><TypeBadge listing={listing} /><span className="text-sm text-gray-500">{listing.category}</span></div>
        <h1 className="text-3xl font-extrabold">{listing.productName}</h1>
        {listing.description && <p className="text-gray-700">{listing.description}</p>}
        {listing.convertedFromDiscount && <Alert kind="info">♻︎ {t("listing.converted")}</Alert>}

        <div className="flex items-baseline gap-3">
          {free ? <span className="text-3xl font-extrabold text-purple-700">{t("listing.free")}</span> : (
            <>
              <span className="text-3xl font-extrabold text-green-800">{lkr(listing.discountedPrice)}</span>
              <span className="text-gray-400 line-through">{lkr(listing.originalPrice)}</span>
            </>
          )}
          <span className="text-sm text-gray-500">/ {listing.unit}</span>
        </div>

        <dl className="card grid grid-cols-2 gap-3 p-4 text-sm">
          <div><dt className="text-gray-500">{t("listing.left")}</dt><dd className="font-semibold">{listing.availableQuantity} / {listing.totalQuantity}</dd></div>
          <div><dt className="text-gray-500">{t("listing.reserveBy")}</dt><dd><Countdown to={listing.reserveBy} /></dd></div>
          <div><dt className="text-gray-500">{t("listing.collectBy")}</dt><dd className="font-semibold">{formatDateTime(listing.collectionDeadline)}</dd></div>
          <div><dt className="text-gray-500">{t("listing.limit")}</dt><dd className="font-semibold">{listing.maxPerCustomer}</dd></div>
          {listing.bestBeforeDate && <div><dt className="text-gray-500">{t("listing.bestBefore")}</dt><dd className="font-semibold">{formatDateTime(listing.bestBeforeDate)}</dd></div>}
        </dl>

        <div className="card space-y-1 p-4 text-sm">
          <p className="font-semibold">{t("listing.pickup")}: {listing.orgName}</p>
          <p className="text-gray-600">{listing.orgAddress}, {listing.orgDistrict}</p>
          {listing.pickupInstructions && <p className="text-gray-600">{listing.pickupInstructions}</p>}
          {listing.orgWhatsapp && (
            <a className="btn-outline mt-2" target="_blank" rel="noreferrer"
              href={waLink(listing.orgWhatsapp, `Hi ${listing.orgName}, I'm interested in "${listing.productName}" on FoodLoop.`)}>💬 {t("whatsapp")}</a>
          )}
        </div>

        {listing.reservable ? (
          !user ? <Link to="/login" className="btn-primary w-full">{t("listing.signinToReserve")}</Link>
          : !profile ? <Link to="/profile" className="btn-primary w-full">{t("listing.completeProfile")}</Link>
          : profile.role === "BUSINESS" ? null
          : !canReserve ? <Alert kind="info">{t("listing.charityOnly")}</Alert>
          : (
            <div className="space-y-3">
              <Field label={t("listing.quantity")}>
                <input type="number" min="1" max={max} value={qty} onChange={(e) => setQty(e.target.value)} className="input max-w-[8rem]" />
              </Field>
              <Alert>{error}</Alert>
              <button className="btn-primary w-full" disabled={busy || qty < 1 || qty > max} onClick={reserve}>
                {t("listing.reserve")} {qty} · {free ? t("listing.free") : lkr(listing.discountedPrice * qty)}
              </button>
              {!free && <p className="text-xs text-gray-500">Pay at the store when you collect.</p>}
            </div>
          )
        ) : <Alert kind="info">{t("listing.closed")}</Alert>}
      </div>
    </div>
  );
}
