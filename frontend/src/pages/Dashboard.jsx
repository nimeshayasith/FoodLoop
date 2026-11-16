import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { Alert, Countdown, Spinner, TypeBadge } from "../components/ui";
import { formatDateTime, lkr } from "../format";

const STATE = {
  SALE_OPEN: ["Sale open", "bg-green-100 text-green-800"],
  SALE_ENDED: ["Sale ended - checking stock", "bg-amber-100 text-amber-900"],
  DONATION_OPEN: ["Donation open", "bg-purple-100 text-purple-800"],
  DONATION_CONVERTED: ["♻︎ Converted to donation", "bg-purple-100 text-purple-800"],
  EXPIRING: ["Closing…", "bg-amber-100 text-amber-900"],
  EXPIRED: ["Closed", "bg-gray-100 text-gray-600"],
};

function PickupBox() {
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState(null);
  async function verify(e) {
    e.preventDefault();
    try {
      const { reservation: r } = await api("/pickup/verify", { method: "POST", auth: true, body: { pickupCode: code } });
      setMsg({ kind: "success", text: `✓ Hand over ${r.quantity} × ${r.productName} to ${r.customerName}` });
      setCode("");
    } catch (err) { setMsg({ kind: "error", text: err.message }); }
  }
  return (
    <form onSubmit={verify} className="card space-y-3 p-5">
      <h2 className="font-semibold">Verify a pickup</h2>
      <div className="flex gap-2">
        <input className="input font-mono uppercase" placeholder="FL-XXXXX" value={code} onChange={(e) => setCode(e.target.value)} required />
        <button className="btn-primary">Verify</button>
      </div>
      {msg && <Alert kind={msg.kind}>{msg.text}</Alert>}
    </form>
  );
}

function ListingRow({ l }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState(null);
  const [label, color] = STATE[l.state] || STATE.EXPIRED;
  const collected = l.collectedQuantity || 0;
  const reserved = l.totalQuantity - l.availableQuantity - collected;
  async function toggle() {
    setOpen(!open);
    if (!open) setRows((await api(`/org/listings/${l.listingId}/reservations`, { auth: true })).reservations);
  }
  return (
    <article className="card space-y-3 p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="mb-1 flex items-center gap-2"><TypeBadge listing={l} /><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${color}`}>{label}</span></div>
          <h3 className="text-lg font-semibold">{l.productName}</h3>
          <p className="text-xs text-gray-500">{l.listingId} · {l.listingType === "DONATION" ? "Free" : lkr(l.discountedPrice)} per {l.unit}</p>
        </div>
        <div className="text-right text-sm">
          {l.status === "ACTIVE" && <Countdown to={l.reserveBy} prefix="Reservations close" />}
          <p className="text-gray-500">Final collection: {formatDateTime(l.collectionDeadline)}</p>
        </div>
      </div>
      <div className="grid grid-cols-4 gap-2 text-center text-sm">
        {[["Total", l.totalQuantity], ["Left", l.availableQuantity], ["Reserved", reserved], ["Collected", collected]].map(([k, v]) => (
          <div key={k} className="rounded-lg bg-gray-50 p-2"><div className="text-lg font-bold">{v}</div><div className="text-xs text-gray-500">{k}</div></div>
        ))}
      </div>
      {l.autoDonateRemaining && <p className="text-xs text-purple-700">♻︎ Unsold stock converts to a free donation{l.donationDeadline ? ` (collect by ${formatDateTime(l.donationDeadline)})` : ""}</p>}
      <button className="text-sm font-semibold text-green-800 underline" onClick={toggle}>{open ? "Hide" : "Show"} reservations</button>
      {open && (rows === null ? <Spinner /> : rows.length === 0 ? <p className="text-sm text-gray-500">No reservations yet.</p> : (
        <ul className="divide-y text-sm">
          {rows.map((r) => (
            <li key={r.reservationId} className="flex justify-between py-2"><span>{r.customerName} ({r.customerRole.toLowerCase()}) · {r.quantity}</span><span className="text-gray-500">{r.reservationStatus}</span></li>
          ))}
        </ul>
      ))}
    </article>
  );
}

export default function Dashboard() {
  const { profile } = useAuth();
  const [listings, setListings] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => api("/org/listings", { auth: true }).then((d) => setListings(d.listings)).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); const id = setInterval(load, 10000); return () => clearInterval(id); }, [load]);
  const approved = profile.status === "APPROVED";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-2xl font-bold">{profile.orgName}</h1><p className="text-sm text-gray-600">{profile.address}, {profile.district}</p></div>
        {approved && <Link to="/dashboard/new" className="btn-primary">+ New listing</Link>}
      </div>
      {!approved && <Alert kind="info">Your business is waiting for verification by the FoodLoop team. You will be able to publish listings once approved.</Alert>}
      <Alert>{error}</Alert>
      {approved && <PickupBox />}
      {!listings ? <Spinner /> : listings.length === 0 ? <p className="py-8 text-center text-gray-500">No listings yet. Publish your first surplus food listing.</p>
        : <div className="grid gap-4 lg:grid-cols-2">{listings.map((l) => <ListingRow key={l.listingId} l={l} />)}</div>}
    </div>
  );
}
