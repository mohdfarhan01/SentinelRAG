import { Link, useLocation } from "react-router-dom";
import BrandMark from "./BrandMark";
import ThemeSwitcher from "./ThemeSwitcher";
import { tierSlug } from "../api";

export default function Sidebar({ user, onLogout }) {
  const location = useLocation();
  const onUpload = location.pathname.startsWith("/app/upload");

  return (
    <aside className="sidebar">
      <Link to="/app" className="sidebar-brand-link">
        <BrandMark />
      </Link>

      <div className="identity-card">
        <div className={`clearance-badge tier-${tierSlug(user.clearance)}`}>
          {user.clearance} clearance
        </div>
        <div className="identity-name">{user.username}</div>
        <div className="identity-line identity-role">
          {user.role} &middot; <span className="identity-department">{user.department}</span>
        </div>
        {user.is_admin && <div className="admin-flag">Admin access</div>}
      </div>

      <nav className="nav">
        <Link className={`nav-item ${!onUpload ? "active" : ""}`} to="/app">
          Ask a question
        </Link>
        {user.is_admin && (
          <Link className={`nav-item ${onUpload ? "active" : ""}`} to="/app/upload">
            Upload documents
          </Link>
        )}
      </nav>

      <ThemeSwitcher className="sidebar-theme-switcher" />

      <button className="logout-btn" onClick={onLogout}>
        Sign out
      </button>
    </aside>
  );
}
