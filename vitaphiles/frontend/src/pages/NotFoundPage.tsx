import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="py-20 text-center">
      <p className="font-display text-6xl">404</p>
      <p className="mt-3 text-ink/60">This page is not in the archive.</p>
      <Link to="/" className="mt-6 inline-block text-wine underline-offset-4 hover:underline">
        Return home
      </Link>
    </div>
  );
}
