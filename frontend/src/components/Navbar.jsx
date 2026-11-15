import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { LANGS, useI18n } from "../i18n";

export default function Navbar() {
  const { user, profile, signOut } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const link = ({ isActive }) => `rounded-md px-3 py-2 text-sm font-medium ${isActive ? "bg-green-100 text-green-800" : "text-gray-700 hover:bg-gray-100"}`;
  const go = () => setOpen(false);

  return (
    <header className="sticky top-0 z-20 border-b bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-xl font-extrabold text-green-800" onClick={go}>
          <span aria-hidden>🍎</span> FoodLoop
        </Link>
        <button className="rounded-md p-2 md:hidden" aria-label="Menu" onClick={() => setOpen(!open)}>☰</button>
        <nav className={`${open ? "flex" : "hidden"} absolute left-0 right-0 top-full flex-col gap-1 border-b bg-white p-3 md:static md:flex md:flex-row md:items-center md:border-0 md:p-0`}>
          <NavLink to="/listings" className={link} onClick={go}>{t("nav.browse")}</NavLink>
          {profile && profile.role !== "BUSINESS" && <NavLink to="/reservations" className={link} onClick={go}>{t("nav.reservations")}</NavLink>}
          {profile?.role === "BUSINESS" && <NavLink to="/dashboard" className={link} onClick={go}>{t("nav.dashboard")}</NavLink>}
          {user?.isAdmin && <NavLink to="/admin" className={link} onClick={go}>{t("nav.admin")}</NavLink>}
          <select aria-label="Language" value={lang} onChange={(e) => setLang(e.target.value)} className="rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm">
            {LANGS.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
          </select>
          {user ? (
            <>
              <NavLink to="/profile" className={link} onClick={go}>{t("nav.profile")}</NavLink>
              <button className="btn-outline" onClick={() => { signOut(); go(); navigate("/"); }}>{t("nav.signout")}</button>
            </>
          ) : (
            <Link to="/login" className="btn-primary" onClick={go}>{t("nav.signin")}</Link>
          )}
        </nav>
      </div>
    </header>
  );
}
