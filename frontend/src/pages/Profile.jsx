import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { Alert, Field } from "../components/ui";
import { BUSINESS_TYPES, DISTRICTS } from "../config";

const ROLES = [
  ["CUSTOMER", "🛒", "I want to buy food", "Browse discounted surplus food and reserve it."],
  ["BUSINESS", "🏪", "I run a food business", "Supermarket, bakery, restaurant or producer with surplus food."],
  ["CHARITY", "🤝", "I represent a charity", "Charity or community group that can collect free food donations."],
];

export default function Profile() {
  const { profile, user, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    role: profile?.role || "CUSTOMER", displayName: profile?.displayName || "", phone: profile?.phone ? `0${profile.phone.slice(2)}` : "",
    district: profile?.district || "Colombo", orgName: profile?.orgName || "", address: profile?.address || "",
    registrationNo: profile?.registrationNo || "", businessType: profile?.businessType || "Supermarket",
  });
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const isOrg = form.role !== "CUSTOMER";
  const locked = profile && profile.role !== "CUSTOMER" && profile.status === "APPROVED";
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function save(e) {
    e.preventDefault();
    setBusy(true); setError(""); setSaved(false);
    try {
      await api("/me", { method: "PUT", auth: true, body: form });
      await refreshProfile();
      setSaved(true);
      if (!profile) navigate(form.role === "BUSINESS" ? "/dashboard" : "/listings");
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }

  return (
    <form onSubmit={save} className="mx-auto max-w-2xl space-y-5">
      <h1 className="text-2xl font-bold">{profile ? "Your profile" : "Welcome! Tell us who you are"}</h1>
      <p className="text-sm text-gray-600">{user?.email}</p>
      {profile?.status === "PENDING" && <Alert kind="info">Your organisation is waiting for verification by the FoodLoop team. You can browse now and publish or reserve donations once approved.</Alert>}
      {profile?.status === "REJECTED" && <Alert>Your organisation could not be verified. Please contact FoodLoop support.</Alert>}

      <div className="grid gap-3 sm:grid-cols-3">
        {ROLES.map(([value, icon, title, text]) => (
          <button type="button" key={value} disabled={locked && value !== form.role} onClick={() => setForm({ ...form, role: value })}
            className={`card p-4 text-left transition ${form.role === value ? "ring-2 ring-green-700" : "hover:bg-gray-50"} disabled:opacity-40`}>
            <div className="text-2xl">{icon}</div><div className="font-semibold">{title}</div><div className="text-xs text-gray-600">{text}</div>
          </button>
        ))}
      </div>

      <div className="card grid gap-4 p-5 sm:grid-cols-2">
        <Field label="Your name"><input className="input" required minLength={2} value={form.displayName} onChange={set("displayName")} /></Field>
        <Field label={isOrg ? "WhatsApp / phone" : "Phone (optional)"} hint="Sri Lankan number, e.g. 0771234567">
          <input className="input" inputMode="tel" required={isOrg} value={form.phone} onChange={set("phone")} />
        </Field>
        <Field label="District">
          <select className="input" value={form.district} onChange={set("district")}>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select>
        </Field>
        {isOrg && (
          <>
            <Field label={form.role === "BUSINESS" ? "Business name" : "Organisation name"}><input className="input" required value={form.orgName} onChange={set("orgName")} /></Field>
            <div className="sm:col-span-2"><Field label="Address"><input className="input" required minLength={5} value={form.address} onChange={set("address")} /></Field></div>
            {form.role === "BUSINESS" && (
              <Field label="Business type"><select className="input" value={form.businessType} onChange={set("businessType")}>{BUSINESS_TYPES.map((b) => <option key={b}>{b}</option>)}</select></Field>
            )}
            <Field label="Registration number (optional)" hint={form.role === "CHARITY" ? "Charity/NGO registration number helps us verify you faster" : "Business registration number"}>
              <input className="input" value={form.registrationNo} onChange={set("registrationNo")} />
            </Field>
          </>
        )}
      </div>
      <Alert>{error}</Alert>
      <Alert kind="success">{saved ? "Saved." : ""}</Alert>
      <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save profile"}</button>
    </form>
  );
}
