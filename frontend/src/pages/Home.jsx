import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { lkr } from "../format";
import { useI18n } from "../i18n";

export default function Home() {
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  useEffect(() => { api("/stats").then(setStats).catch(() => {}); }, []);

  return (
    <div className="space-y-10">
      <section className="rounded-2xl bg-gradient-to-br from-green-700 to-green-900 px-6 py-12 text-white md:px-12">
        <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-green-200">🍎 FoodLoop</p>
        <h1 className="max-w-2xl text-3xl font-extrabold leading-tight md:text-5xl">{t("tagline")}</h1>
        <p className="mt-4 max-w-2xl text-lg text-green-100">{t("hero.sub")}</p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/listings" className="btn-primary !bg-white text-green-900 hover:bg-green-50">{t("cta.browse")}</Link>
          <Link to="/profile" className="btn-outline !border-white/60 !bg-transparent text-white hover:bg-white/10">{t("cta.list")}</Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[["stats.rescued", stats?.itemsRescued ?? 0, "🥖"], ["stats.donated", stats?.itemsDonated ?? 0, "🤝"], ["stats.saved", lkr(stats?.lkrSaved ?? 0), "💸"]].map(([key, value, icon]) => (
          <div key={key} className="card p-5 text-center">
            <div className="text-3xl">{icon}</div>
            <div className="mt-1 text-2xl font-extrabold text-green-800">{value}</div>
            <div className="text-sm text-gray-600">{t(key)}</div>
          </div>
        ))}
      </section>

      <section>
        <h2 className="mb-4 text-2xl font-bold">{t("how.title")}</h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {["how.1", "how.2", "how.3"].map((key, i) => (
            <li key={key} className="card flex gap-4 p-5">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-green-100 font-bold text-green-800">{i + 1}</span>
              <p>{t(key)}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
