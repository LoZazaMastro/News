import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
let ts;
try {
  ts = require("typescript");
} catch {
  // Fallback used by the artifact build environment. Normal project builds use
  // the local devDependency above.
  ts = require("/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript/lib/typescript.js");
}
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourcePath = path.join(root, "src", "index.tsx");
const outPath = path.join(root, "dist", "index.js");
const source = fs.readFileSync(sourcePath, "utf8");
const result = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.ESNext,
    jsx: ts.JsxEmit.React,
    jsxFactory: "SP_REACT.createElement",
    jsxFragmentFactory: "SP_REACT.Fragment",
    removeComments: false,
    esModuleInterop: true,
  },
  fileName: "index.tsx",
  reportDiagnostics: true,
});
if (result.diagnostics?.length) {
  const fatal = result.diagnostics.filter((diag) => diag.category === ts.DiagnosticCategory.Error);
  if (fatal.length) {
    for (const diag of fatal) console.error(ts.flattenDiagnosticMessageText(diag.messageText, "\n"));
    process.exit(1);
  }
}
let body = result.outputText.replace(/^import[^;]+;\s*$/gm, "").trimStart();
const preamble = `const manifest = {"name":"News"};
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) throw new Error("[@decky/api]: Decky Loader API is unavailable.");
let api;
try { api = internalAPIConnection.connect(API_VERSION, manifest.name); }
catch { api = internalAPIConnection.connect(1, manifest.name); console.warn("[News] Falling back to Decky API v1."); }
const call = api.call;
const routerHook = api.routerHook;
const definePlugin = (fn) => (...args) => fn(...args);
const { DialogButton, Focusable, GamepadButton, Navigation, PanelSection, PanelSectionRow, Router, TextField, findModuleExport } = DFL;
const { memo, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } = SP_REACT;
`;
fs.mkdirSync(path.dirname(outPath), { recursive: true });
fs.writeFileSync(outPath, preamble + "\n" + body, "utf8");
console.log(`Built ${outPath}`);
