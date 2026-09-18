import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import SignIn from "./components/SignIn";
import SignUp from "./components/SignUp";
import Sidebar from "./components/Sidebar";
import ChatView from "./components/ChatView";
import AdminUpload from "./components/AdminUpload";

const STORAGE_KEY = "sentinelrag_session";

function readStoredSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function AppShell({ token, user, onLogout, view }) {
  return (
    <div className="app-shell">
      <Sidebar user={user} onLogout={onLogout} />
      <div className="app-main">
        {view === "upload" ? <AdminUpload token={token} /> : <ChatView token={token} />}
      </div>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState(readStoredSession);

  useEffect(() => {
    try {
      if (session) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Storage may be unavailable (private browsing, blocked cookies).
      // The session still works for this tab; it just won't persist.
    }
  }, [session]);

  function handleLoggedIn(result) {
    setSession({ token: result.access_token, user: result.user });
  }

  function handleLogout() {
    setSession(null);
  }

  return (
    <Routes>
      <Route path="/" element={session ? <Navigate to="/app" replace /> : <LandingPage />} />
      <Route
        path="/signin"
        element={session ? <Navigate to="/app" replace /> : <SignIn onLoggedIn={handleLoggedIn} />}
      />
      <Route
        path="/signup"
        element={session ? <Navigate to="/app" replace /> : <SignUp onLoggedIn={handleLoggedIn} />}
      />
      <Route
        path="/app"
        element={
          session ? (
            <AppShell token={session.token} user={session.user} onLogout={handleLogout} view="chat" />
          ) : (
            <Navigate to="/signin" replace />
          )
        }
      />
      <Route
        path="/app/upload"
        element={
          !session ? (
            <Navigate to="/signin" replace />
          ) : session.user.is_admin ? (
            <AppShell token={session.token} user={session.user} onLogout={handleLogout} view="upload" />
          ) : (
            <Navigate to="/app" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
