import { useEffect, useState } from "react";
import LoginScreen from "./components/LoginScreen";
import Sidebar from "./components/Sidebar";
import ChatView from "./components/ChatView";
import AdminUpload from "./components/AdminUpload";

const STORAGE_KEY = "sentinelrag_session";

export default function App() {
  const [session, setSession] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  });
  const [view, setView] = useState("chat");

  useEffect(() => {
    if (session) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [session]);

  if (!session) {
    return (
      <LoginScreen
        onLoggedIn={(result) =>
          setSession({ token: result.access_token, user: result.user })
        }
      />
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        user={session.user}
        view={view}
        onNavigate={setView}
        onLogout={() => setSession(null)}
      />
      {view === "admin" && session.user.is_admin ? (
        <AdminUpload token={session.token} />
      ) : (
        <ChatView token={session.token} />
      )}
    </div>
  );
}
