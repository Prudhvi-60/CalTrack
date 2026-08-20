export function ErrorAlert({ message }: { message: string }) {
  return (
    <div className="border border-wine/30 bg-wine/5 px-3 py-2 text-sm text-wine" role="alert">
      {message}
    </div>
  );
}
