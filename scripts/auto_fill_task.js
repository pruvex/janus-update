import fs from "fs";
import path from "path";

const TEMPLATE_PATH = ".cursor/templates/diamond_task_template.mdc";
const TASK_FOLDER = "documentation/tasks/";

function getFormattedDate() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function generateTaskID() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,"0")}${String(d.getDate()).padStart(2,"0")}-${Math.floor(Math.random() * 90 + 10)}`;
}

if (!fs.existsSync(TEMPLATE_PATH)) { process.exit(1); }
let template = fs.readFileSync(TEMPLATE_PATH, "utf-8");
const taskID = generateTaskID();
const dateTime = getFormattedDate();
template = template.replace(/\[TASK-NAME\]/g, process.argv[2] || "NEUER-TASK").replace(/\[YYYYMMDD-XX\]/g, taskID).replace(/\[YYYY-MM-DD HH:MM\]/g, dateTime).replace(/\[YYYY-MM-DD\]/g, dateTime.split(' ')[0]);
if (!fs.existsSync(TASK_FOLDER)) fs.mkdirSync(TASK_FOLDER, { recursive: true });
fs.writeFileSync(path.join(TASK_FOLDER, `task_${taskID}.md`), template);
console.log(`✅ Diamond-Task erstellt.`);
