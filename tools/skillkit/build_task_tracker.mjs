import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "D:/GitProject/Unity-AI-Instructions/outputs/task-tracker";
const outputPath = `${outputDir}/roblox-clone-fix-tracker.xlsx`;

const rows = [
  ["UI Layout", "P1", "BtnPet / Bag order", "Move BtnPet to the bottom, with Bag directly above it.", "BtnPet is lowest; Bag is immediately above; verify at target aspect ratios.", "", "", false],
  ["UI Layout", "P1", "Free Cash panel", "Increase the Free Cash panel size; current panel is too small.", "Panel is readable and matches the reference capture without overlap.", "", "", false],
  ["UI Layout", "P1", "HP bar padding", "Make progress fill padding even against the background.", "Left/right/top/bottom padding is visually equal in screenshot comparison.", "", "", false],
  ["Gameplay", "P2", "Remove weapon switching", "Evaluate removing the weapon system because the hammer already handles smashing.", "Decision recorded; if removed, no dead weapon UI/input path remains.", "", "", false],
  ["Gameplay", "P1", "Egg auto-smash", "If the player touches an egg without moving, automatically smash it.", "Touching an egg while stationary triggers the correct smash flow once.", "", "", false],
  ["UI Layout", "P1", "Egg info text", "Increase Egg info text size by 50%.", "Text remains readable, aligned and does not clip at supported aspect ratios.", "", "", false],
  ["Pet UI", "P1", "PopupPet scale and layout", "Enlarge PopupPet; align BtnEquipBest to the right; add Auto EquipBest checkbox on the left, default true.", "Popup is larger; button is right-aligned; checkbox defaults true and persists during the popup session.", "", "", false],
  ["Pet System", "P0", "Full cage pet handoff", "When the cage is full, the carried pet must not disappear; dropping it should fly into BtnPet with Scale In after checking Auto EquipBest.", "Full-cage behavior is recoverable; dropped pet enters the intended cage/queue and BtnPet animates.", "", "", false],
  ["Shop", "P1", "Shop pet avatar white icon", "Fix the white/missing icon on pet avatars in the shop.", "All shop pet avatars render their intended icon in Play Mode.", "", "", false],
  ["Shop", "P2", "Treadmill/cage upgrade reward button", "Add the reward button to treadmill and cage upgrade panels.", "Reward button is visible, clickable and grants the intended reward once.", "", "", false],
  ["Monetization", "P1", "IAP machine", "Add the IAP machine flow.", "Catalog, purchase callback, grant path and failure state are wired and tested.", "", "", false],
  ["Shop", "P1", "Move shop closer", "Reduce the distance between the player and the shop.", "Player can reach and read the shop comfortably; capture confirms intended placement.", "", "", false],
  ["Shop", "P2", "Reward button for next owned max item", "For the next item after the max item currently owned, add the reward button.", "Correct next-item state shows the reward button and no invalid purchase action.", "", "", false],
  ["Inventory UI", "P2", "Remove five bottom slots", "Evaluate removing the five bottom slots because they have little use.", "Decision recorded; if removed, layout and navigation have no empty dead area.", "", "", false],
  ["Pet Art", "P1", "AI repair non-policy pets", "Use AI-assisted revision for pets that do not meet the visual policy.", "Each revised pet passes the visual/policy checklist and asset provenance is recorded.", "", "", false],
  ["Pet System", "P1", "Pet drop flight", "When a pet is dropped, make it fly down beside the player.", "Pet follows the intended arc and lands beside the player without disappearing.", "", "", false],
  ["Onboarding", "P1", "First pet to treadmill", "After collecting the first pet, route the player to the treadmill.", "First-pet milestone triggers the treadmill guidance exactly once.", "", "", false],
  ["Editor Tools", "P1", "Info view position tool", "Create an editor tool to arrange info-view positions cleanly; camel info is currently too high and should sit near its back.", "Tool is repeatable; camel and representative pets have hand-tunable positions with before/after screenshots.", "", "", false],
  ["Pet Art", "P1", "Wing rotation", "Fix pets whose wings are rotated at the wrong angle.", "Affected pets match the reference orientation in Play Mode.", "", "", false],
  ["Gameplay / QA", "P0", "Invisible BOT pet theft", "Investigate invisible BOTs that appear after playing for a while and steal pets.", "Reproduce, identify root cause, fix, and verify after an extended session; no invisible BOT or unauthorized theft.", "", "", false],
];

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Task Tracker");
sheet.showGridLines = false;
sheet.tabColor = "#1F4E78";

sheet.getRange("A1:H1").merge();
sheet.getRange("A1").values = [["Roblox Clone Fix Tracker"]];
sheet.getRange("A2:H2").merge();
sheet.getRange("A2").values = [["Upload to Google Sheets, then convert the Done? column to checkboxes. Keep the acceptance criteria as the completion gate."]];
sheet.getRange("A4:H4").values = [["Group", "Priority", "Task", "Requirement", "Acceptance criteria", "Owner", "Notes", "Done?"]];
sheet.getRange(`A5:H${rows.length + 4}`).values = rows;

const header = sheet.getRange("A4:H4");
header.format = { fill: "#1F4E78", font: { color: "#FFFFFF", bold: true }, verticalAlignment: "center", wrapText: true, borders: { preset: "all", style: "thin", color: "#D9E2F3" } };
sheet.getRange("A1:H1").format = { font: { bold: true, size: 16, color: "#1F1F1F" }, verticalAlignment: "center" };
sheet.getRange("A2:H2").format = { font: { italic: true, color: "#666666" }, wrapText: true };
sheet.getRange(`A5:H${rows.length + 4}`).format = { verticalAlignment: "center", wrapText: true, borders: { insideHorizontal: { style: "thin", color: "#E6E6E6" } } };
sheet.getRange(`H5:H${rows.length + 4}`).format = { horizontalAlignment: "center", verticalAlignment: "center", fill: "#FFF2CC" };
sheet.getRange(`B5:B${rows.length + 4}`).dataValidation = { rule: { type: "list", values: ["P0", "P1", "P2"] } };
sheet.getRange(`H5:H${rows.length + 4}`).dataValidation = { rule: { type: "list", values: ["TRUE", "FALSE"] } };

sheet.getRange("A:A").format.columnWidth = 18;
sheet.getRange("B:B").format.columnWidth = 10;
sheet.getRange("C:C").format.columnWidth = 28;
sheet.getRange("D:D").format.columnWidth = 48;
sheet.getRange("E:E").format.columnWidth = 58;
sheet.getRange("F:F").format.columnWidth = 16;
sheet.getRange("G:G").format.columnWidth = 28;
sheet.getRange("H:H").format.columnWidth = 10;
sheet.getRange("A1:H1").format.rowHeight = 28;
sheet.getRange("A2:H2").format.rowHeight = 30;
sheet.getRange("A4:H4").format.rowHeight = 34;
sheet.getRange(`A5:H${rows.length + 4}`).format.rowHeight = 42;
sheet.freezePanes.freezeRows(4);

sheet.getRange(`B5:B${rows.length + 4}`).conditionalFormats.add("containsText", { text: "P0", format: { fill: "#F4CCCC", font: { bold: true, color: "#9C0006" } } });
sheet.getRange(`B5:B${rows.length + 4}`).conditionalFormats.add("containsText", { text: "P1", format: { fill: "#FCE5CD", font: { bold: true, color: "#7F6000" } } });

workbook.recalculate();
const check = await workbook.inspect({ kind: "table", sheetId: "Task Tracker", range: "A1:H24", include: "values,formulas", tableMaxRows: 24, tableMaxCols: 8, maxChars: 8000 });
console.log(check.ndjson);
const preview = await workbook.render({ sheetName: "Task Tracker", range: "A1:H12", scale: 1, format: "png" });
await fs.mkdir(outputDir, { recursive: true });
await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`WROTE ${outputPath}`);
