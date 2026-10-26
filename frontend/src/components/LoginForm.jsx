import { useState } from "react";

export default function LoginForm({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await onLogin(email, password);
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="dashboard-shell login-shell">
      <section className="login-card" aria-labelledby="login-title">
        <a className="logo" href="/" aria-label="CloudTask dashboard"><span className="logo-mark" aria-hidden="true">C</span><span>CloudTask</span></a>
        <p className="eyebrow">OPERATOR ACCESS</p>
        <h1 id="login-title">Sign in to CloudTask</h1>
        <p>Use the operator account configured during installation.</p>
        <form onSubmit={submit} className="login-form">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required />
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          {error && <p className="notice error" role="alert">{error}</p>}
          <button type="submit" disabled={submitting}>{submitting ? "Signing in…" : "Sign in"}</button>
        </form>
      </section>
    </main>
  );
}
