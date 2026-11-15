import "@decky/ui/dist/components/Dialog";
import type { FocusEventHandler } from "react";

// Steam's native DialogButton forwards these DOM attributes; @decky/ui 4.12
// omits them from its declaration. This only describes existing calls.
declare module "@decky/ui/dist/components/Dialog" {
  interface DialogButtonProps {
    onFocus?: FocusEventHandler<HTMLDivElement>;
    title?: string;
  }
}
