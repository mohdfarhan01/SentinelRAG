import BrandMark from "./BrandMark";
import { tierSlug } from "../api";

export default function Sidebar({ user, view, onNavigate, onLogout }) {
  return (
    <aside className="sidebar">
      <BrandMark />

      <div className="identity-card">
        <div className="identity-name">{user.username}</div>
        <div className="identity-line identity-role">{user.role}</div>
        <div className="identity-line identity-department">{user.department}</div>
        <div className={`clearance-badge tier-${tierSlug(user.clearance)}`}>
          {user.clearance}
        </div>
        {user.is_admin && <div className="admin-flag">Admin access</div>}
      </div>

      <nav className="nav">
        <button
          className={`nav-item ${view === "chat" ? "active" : ""}`}
          onClick={() => onNavigate("chat")}
        >
          Ask a question
        </button>
        {user.is_admin && (
          <button
            className={`nav-item ${view === "admin" ? "active" : ""}`}
            onClick={() => onNavigate("admin")}
          >
            Upload documents
          </button>
        )}
      </nav>

      <button className="logout-btn" onClick={onLogout}>
        Sign out
      </button>
    </aside>
  );
}
