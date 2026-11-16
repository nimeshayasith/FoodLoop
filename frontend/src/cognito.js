// Minimal Amazon Cognito client (public app client, no secret) using plain fetch - no SDK needed.
import { CLIENT_ID, REGION } from "./config";

const ENDPOINT = `https://cognito-idp.${REGION}.amazonaws.com/`;
const KEY = "foodloop.auth";

async function idp(target, body) {
  let res;
  try {
    res = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/x-amz-json-1.1", "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}` },
      body: JSON.stringify({ ClientId: CLIENT_ID, ...body }),
    });
  } catch {
    throw new CognitoError("Network problem - check your connection", "network");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const code = (data.__type || "").split("#").pop();
    throw new CognitoError(friendly(code, data.message), code);
  }
  return data;
}

export class CognitoError extends Error {
  constructor(message, code) { super(message); this.code = code; }
}

function friendly(code, fallback) {
  return ({
    UsernameExistsException: "An account with this email already exists - sign in instead.",
    InvalidPasswordException: "Password needs 8+ characters with upper-case, lower-case and a number.",
    NotAuthorizedException: "Wrong email or password.",
    UserNotConfirmedException: "Please confirm your email first.",
    CodeMismatchException: "That code is not correct.",
    ExpiredCodeException: "That code has expired - request a new one.",
    LimitExceededException: "Too many attempts - please wait a few minutes.",
    TooManyRequestsException: "Too many attempts - please wait a few minutes.",
    InvalidParameterException: fallback || "Please check your details.",
  })[code] || fallback || "Something went wrong";
}

export const signUp = (email, password) =>
  idp("SignUp", { Username: email, Password: password, UserAttributes: [{ Name: "email", Value: email }] });
export const confirmSignUp = (email, code) => idp("ConfirmSignUp", { Username: email, ConfirmationCode: code });
export const resendCode = (email) => idp("ResendConfirmationCode", { Username: email });

function store(result, previous) {
  const session = {
    idToken: result.IdToken,
    refreshToken: result.RefreshToken || previous?.refreshToken,
    expiresAt: Date.now() + (result.ExpiresIn || 3600) * 1000,
  };
  localStorage.setItem(KEY, JSON.stringify(session));
  return session;
}

export async function signIn(email, password) {
  const data = await idp("InitiateAuth", { AuthFlow: "USER_PASSWORD_AUTH", AuthParameters: { USERNAME: email, PASSWORD: password } });
  return store(data.AuthenticationResult);
}

export const signOut = () => localStorage.removeItem(KEY);

function read() {
  try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; }
}

/** Returns a valid ID token (refreshing it when it is about to expire) or null. */
export async function getToken() {
  const session = read();
  if (!session) return null;
  if (session.expiresAt - 60_000 > Date.now()) return session.idToken;
  try {
    const data = await idp("InitiateAuth", { AuthFlow: "REFRESH_TOKEN_AUTH", AuthParameters: { REFRESH_TOKEN: session.refreshToken } });
    return store(data.AuthenticationResult, session).idToken;
  } catch {
    signOut();
    return null;
  }
}

export function tokenClaims(token) {
  try {
    const payload = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(escape(atob(payload))));
  } catch { return {}; }
}
