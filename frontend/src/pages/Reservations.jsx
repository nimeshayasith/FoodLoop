import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Alert, Spinner, waLink } from "../components/ui";
import { formatDateTime, lkr } from "../format";
import { useI18n } from "../i18n";

const color = { RESERVED: "bg-green-100 text-green-800", COLLECTED: "bg-blue-100 text-blue-800", CANCELLED: "bg-gray-100 text-gray-600", NO_SHOW: "bg-red-100 text-red-700" };

export default function Reservations() {
  const { t } = useI18n();
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => api("/me/reservations", { auth: true }).then((d) => setItems(d.reservations)).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  async function cancel(id) {
    if (!confirm("Cancel this reservation?")) return;
    try { await api(`/reservations/${id}/cancel`, { method: "POST", auth: true }); load(); } catch (e) { setError(e.message); }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">{t("res.title")}</h1>
      <Alert>{error}</Alert>
      {!items ? <Spinner /> : items.length === 0 ? (
        <p className="py-10 text-center text-gray-500">{t("res.empty")} <Link className="font-semibold text-green-800 underline" to="/listings">{t("nav.browse")}</Link></p>
      ) : items.map((r) => (
        <article key={r.reservationId} className="card space-y-3 p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{r.quantity} × {r.productName}</h2>
              <p className="text-sm text-gray-600">{r.orgName} · {r.orgAddress}</p>
            </div>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${color[r.reservationStatus]}`}>{t(`status.${r.reservationStatus}`)}</span>
          </div>
          {r.reservationStatus === "RESERVED" && (
            <div className="rounded-lg bg-green-50 p-4 text-center">
              <p className="text-xs uppercase tracking-wide text-green-800">{t("res.code")}</p>
              <p className="font-mono text-3xl font-extrabold tracking-widest text-green-900">{r.pickupCode.slice(0, 2)}-{r.pickupCode.slice(2)}</p>
              <p className="text-xs text-green-800">{t("res.show")}</p>
            </div>
          )}
          <p className="text-sm text-gray-700">{t("listing.collectBy")}: <strong>{formatDateTime(r.pickupBy)}</strong> · {r.totalPrice > 0 ? lkr(r.totalPrice) : t("listing.free")}</p>
          <div className="flex flex-wrap gap-2">
            {r.orgWhatsapp && <a className="btn-outline" target="_blank" rel="noreferrer" href={waLink(r.orgWhatsapp, `Hi ${r.orgName}, about my FoodLoop reservation ${r.pickupCode}`)}>💬 {t("whatsapp")}</a>}
            {r.canCancel && <button className="btn-danger" onClick={() => cancel(r.reservationId)}>{t("res.cancel")}</button>}
          </div>
        </article>
      ))}
    </div>
  );
}
