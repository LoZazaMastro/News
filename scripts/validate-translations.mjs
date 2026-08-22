import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const catalogs=JSON.parse(fs.readFileSync(path.join(root,"src","locales.json"),"utf8"));
const locales=Object.keys(catalogs);
if(locales.length!==9) throw new Error(`Expected Italian + 8 additional locales, found ${locales.length}: ${locales.join(", ")}`);
const base=Object.keys(catalogs.en).sort();
const placeholders=(value)=>[...String(value).matchAll(/\{([A-Za-z0-9_]+)\}/g)].map(m=>m[1]).sort();
for(const locale of locales){
  const keys=Object.keys(catalogs[locale]).sort();
  if(JSON.stringify(keys)!==JSON.stringify(base)) throw new Error(`${locale}: translation keys do not match English catalog`);
  for(const key of base){
    const value=String(catalogs[locale][key]??"").trim();
    if(!value) throw new Error(`${locale}.${key}: empty translation`);
    const expected=placeholders(catalogs.en[key]);
    const actual=placeholders(value);
    if(JSON.stringify(expected)!==JSON.stringify(actual)) throw new Error(`${locale}.${key}: placeholder mismatch ${actual} != ${expected}`);
  }
}
console.log(`Translations OK: ${locales.length} locales, ${base.length} keys each.`);
