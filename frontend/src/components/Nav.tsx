import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export function Nav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark" />
          IPL Book
        </Link>

        <nav className="nav-links">
          <NavLink to="/" end>
            Matches
          </NavLink>
          {user && <NavLink to="/bookings">My bookings</NavLink>}
          {user?.is_admin && <NavLink to="/admin">Admin</NavLink>}
          <NavLink to="/architecture">How it works</NavLink>
        </nav>

        <div className="nav-user">
          {user ? (
            <>
              <span>{user.name}</span>
              <button
                className="btn small ghost"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <Link to="/login" className="btn small primary">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
