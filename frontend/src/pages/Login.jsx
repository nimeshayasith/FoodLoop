import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import * as cognito from "../cognito";
import { Alert, Field } from "../components/ui";
import { useI18n } from "../i18n";

export default function Login() {
  const { signIn } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [mode, setMode] = useState("signin"); // signin | signup | confirm
  const [form, setForm] = useState({ email: "", password: "", code: "" });
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(""); setInfo("");
    const email = form.email.trim().toLowerCase();
    try {
      if (mode === "signup") {
        await cognito.signUp(email, form.password);
        setMode("confirm"); setInfo("We emailed you a 6-digit code. Enter it below.");
      } else if (mode === "confirm") {
        await cognito.confirmSignUp(email, form.code.trim());
        await signIn(email, form.password);
        navigate("/profile");
      } else {
        await signIn(email, form.password);
        navigate("/listings");
      }
    } catch (err) {
      if (err.code === "UserNotConfirmedException") { setMode("confirm"); setInfo("Enter the code we emailed you."); cognito.resendCode(email).catch(() => {}); }
      else setError(err.message);
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto max-w-md">
      <form onSubmit={submit} className="card space-y-4 p-6">
        <h1 className="text-2xl font-bold">{mode === "signup" ? "Create your account" : mode === "confirm" ? "Confirm your email" : t("nav.signin")}</h1>
        <Alert kind="success">{info}</Alert>
        <Alert>{error}</Alert>
        <Field label="Email"><input className="input" type="email" required autoComplete="email" value={form.email} onChange={set("email")} /></Field>
        <Field label="Password" hint={mode === "signup" ? "8+ characters with upper-case, lower-case and a number" : undefined}>
          <input className="input" type="password" required minLength={8} autoComplete={mode === "signin" ? "current-password" : "new-password"} value={form.password} onChange={set("password")} />
        </Field>
        {mode === "confirm" && <Field label="Verification code"><input className="input" inputMode="numeric" required value={form.code} onChange={set("code")} /></Field>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "…" : mode === "signup" ? "Create account" : mode === "confirm" ? "Confirm" : t("nav.signin")}</button>
        {mode !== "confirm" && (
          <p className="text-center text-sm text-gray-600">
            {mode === "signin" ? "New to FoodLoop? " : "Already have an account? "}
            <button type="button" className="font-semibold text-green-800 underline" onClick={() => { setMode(mode === "signin" ? "signup" : "signin"); setError(""); }}>
              {mode === "signin" ? "Create an account" : t("nav.signin")}
            </button>
          </p>
        )}
      </form>
    </div>
  );
}
