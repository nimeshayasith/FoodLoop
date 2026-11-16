import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { Alert, Field } from "../components/ui";
import { CATEGORIES } from "../config";
import { localInputToIso, localInputValue } from "../format";

export default function NewListing() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    listingType: "DISCOUNTED", productName: "", description: "", category: "Bakery", unit: "packet", totalQuantity: 20,
    originalPrice: 200, discountedPrice: 100, maxPerCustomer: 5, autoDonateRemaining: true,
    saleDeadline: localInputValue(180), collectionDeadline: localInputValue(240), donationDeadline: localInputValue(360), bestBeforeDate: "",
    pickupInstructions: "",
  });
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const discounted = form.listingType === "DISCOUNTED";

  // Short timings so the whole Step Functions lifecycle can be shown in a live demo.
  const demoTimings = () => setForm({ ...form, listingType: "DISCOUNTED", autoDonateRemaining: true, saleDeadline: localInputValue(2), collectionDeadline: localInputValue(3), donationDeadline: localInputValue(6) });

  async function uploadImage() {
    if (!file) return undefined;
    if (file.size > 3 * 1024 * 1024) throw new Error("Image must be under 3 MB");
    const { url, fields, key } = await api("/uploads/presign", { method: "POST", auth: true, body: { contentType: file.type } });
    const data = new FormData();
    Object.entries(fields).forEach(([k, v]) => data.append(k, v));
    data.append("file", file); // must be last
    const res = await fetch(url, { method: "POST", body: data });
    if (!res.ok) throw new Error("Image upload failed");
    return key;
  }

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const imageKey = await uploadImage();
      const body = {
        listingType: form.listingType, productName: form.productName, description: form.description, category: form.category,
        unit: form.unit, totalQuantity: Number(form.totalQuantity), maxPerCustomer: Number(form.maxPerCustomer),
        pickupInstructions: form.pickupInstructions, collectionDeadline: localInputToIso(form.collectionDeadline),
        bestBeforeDate: form.bestBeforeDate ? localInputToIso(form.bestBeforeDate) : undefined, imageKey,
      };
      if (discounted) {
        Object.assign(body, {
          originalPrice: Number(form.originalPrice), discountedPrice: Number(form.discountedPrice),
          saleDeadline: localInputToIso(form.saleDeadline), autoDonateRemaining: form.autoDonateRemaining,
          donationDeadline: form.autoDonateRemaining ? localInputToIso(form.donationDeadline) : undefined,
        });
      }
      await api("/listings", { method: "POST", auth: true, body });
      navigate("/dashboard");
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="mx-auto max-w-2xl space-y-5">
      <h1 className="text-2xl font-bold">New listing</h1>
      <div className="grid grid-cols-2 gap-3">
        {[["DISCOUNTED", "🏷️ Smart deal", "Sell surplus at a reduced price"], ["DONATION", "🤝 Free donation", "Give food to verified charities"]].map(([v, title, text]) => (
          <button type="button" key={v} onClick={() => setForm({ ...form, listingType: v })} className={`card p-4 text-left ${form.listingType === v ? "ring-2 ring-green-700" : "hover:bg-gray-50"}`}>
            <div className="font-semibold">{title}</div><div className="text-xs text-gray-600">{text}</div>
          </button>
        ))}
      </div>

      <div className="card grid gap-4 p-5 sm:grid-cols-2">
        <div className="sm:col-span-2"><Field label="Product name"><input className="input" required minLength={2} maxLength={80} value={form.productName} onChange={set("productName")} placeholder="Bread packets" /></Field></div>
        <div className="sm:col-span-2"><Field label="Description (optional)"><textarea className="input" maxLength={300} rows={2} value={form.description} onChange={set("description")} /></Field></div>
        <Field label="Category"><select className="input" value={form.category} onChange={set("category")}>{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></Field>
        <Field label="Unit"><input className="input" maxLength={20} value={form.unit} onChange={set("unit")} /></Field>
        <Field label="Quantity available"><input className="input" type="number" min="1" max="10000" required value={form.totalQuantity} onChange={set("totalQuantity")} /></Field>
        <Field label="Max per customer"><input className="input" type="number" min="1" required value={form.maxPerCustomer} onChange={set("maxPerCustomer")} /></Field>
        {discounted && (
          <>
            <Field label="Original price (LKR)"><input className="input" type="number" min="1" step="0.01" required value={form.originalPrice} onChange={set("originalPrice")} /></Field>
            <Field label="Discounted price (LKR)"><input className="input" type="number" min="1" step="0.01" required value={form.discountedPrice} onChange={set("discountedPrice")} /></Field>
            <Field label="Sale ends (last time to reserve)"><input className="input" type="datetime-local" required value={form.saleDeadline} onChange={set("saleDeadline")} /></Field>
          </>
        )}
        <Field label={discounted ? "Customer pickup deadline" : "Collection deadline"}><input className="input" type="datetime-local" required value={form.collectionDeadline} onChange={set("collectionDeadline")} /></Field>
        <Field label="Best before / use by (optional)" hint="Pickup deadlines can never be after this time"><input className="input" type="datetime-local" value={form.bestBeforeDate} onChange={set("bestBeforeDate")} /></Field>
        <div className="sm:col-span-2"><Field label="Pickup instructions (optional)"><input className="input" maxLength={200} value={form.pickupInstructions} onChange={set("pickupInstructions")} placeholder="Ask at the bakery counter" /></Field></div>
        <div className="sm:col-span-2"><Field label="Photo (optional, JPG/PNG/WebP, max 3 MB)"><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files[0] || null)} /></Field></div>
      </div>

      {discounted && (
        <div className="card space-y-3 border-purple-200 bg-purple-50 p-5">
          <label className="flex items-start gap-3">
            <input type="checkbox" className="mt-1 h-4 w-4" checked={form.autoDonateRemaining} onChange={set("autoDonateRemaining")} />
            <span><strong>♻︎ Donate unsold items automatically</strong><br /><span className="text-sm text-gray-700">When the sale ends, leftover stock becomes a free donation for verified charities.</span></span>
          </label>
          {form.autoDonateRemaining && (
            <Field label="Donation collection deadline" hint="Must be after the customer pickup deadline"><input className="input" type="datetime-local" required value={form.donationDeadline} onChange={set("donationDeadline")} /></Field>
          )}
        </div>
      )}

      <Alert>{error}</Alert>
      <div className="flex flex-wrap gap-3">
        <button className="btn-primary" disabled={busy}>{busy ? "Publishing…" : "Publish listing"}</button>
        {discounted && <button type="button" className="btn-outline" onClick={demoTimings}>⚡ Demo timings (2 / 3 / 6 min)</button>}
      </div>
    </form>
  );
}
