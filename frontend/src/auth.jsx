import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";
import * as cognito from "./cognito";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // { email, isAdmin }
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const token = await cognito.getToken();
    if (!token) { setUser(null); setProfile(null); setLoading(false); return; }
    const claims = cognito.tokenClaims(token);
    setUser({ email: claims.email, isAdmin: (claims["cognito:groups"] || []).includes("admin") });
    try {
      const me = await api("/me", { auth: true });
      setProfile(me.profile);
    } catch { setProfile(null); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const value = {
    user, profile, loading,
    refreshProfile: load,
    async signIn(email, password) { await cognito.signIn(email, password); await load(); },
    signOut() { cognito.signOut(); setUser(null); setProfile(null); },
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
