import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { Alert, Spinner } from "../components/ui";

export default function Admin() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => api("/admin/profiles?status=PENDING", { auth: true }).then((d) => setRows(d.profiles)).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load]);

  async function decide(userId, decision) {
    try { await api(`/admin/profiles/${userId}/decision`, { method: "POST", auth: true, body: { decision } }); load(); } catch (e) { setError(e.message); }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-bold">Organisations waiting for verification</h1>
      <Alert>{error}</Alert>
      {!rows ? <Spinner /> : rows.length === 0 ? <p className="py-8 text-center text-gray-500">Nothing to review 🎉</p> : rows.map((p) => (
        <article key={p.userId} className="card flex flex-wrap items-center justify-between gap-3 p-5">
          <div className="text-sm">
            <p className="text-lg font-semibold">{p.orgName} <span className="text-xs font-normal text-gray-500">({p.role.toLowerCase()})</span></p>
            <p>{p.address}, {p.district}</p>
            <p className="text-gray-600">{p.displayName} · {p.email} · 0{String(p.phone).slice(2)}</p>
            {p.registrationNo && <p className="text-gray-600">Reg. no: {p.registrationNo}</p>}
          </div>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={() => decide(p.userId, "APPROVE")}>Approve</button>
            <button className="btn-danger" onClick={() => decide(p.userId, "REJECT")}>Reject</button>
          </div>
        </article>
      ))}
    </div>
  );
}
