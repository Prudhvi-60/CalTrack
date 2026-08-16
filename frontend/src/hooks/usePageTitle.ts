import { useEffect } from "react";

export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} · CalTrack`;
    return () => {
      document.title = "CalTrack";
    };
  }, [title]);
}
