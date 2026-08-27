const { existsSync, readdirSync } = require("node:fs");
const { join } = require("node:path");
const { spawn } = require("node:child_process");

function findUv() {
  const command = process.platform === "win32" ? "uv.exe" : "uv";
  const localAppData = process.env.LOCALAPPDATA;

  if (localAppData) {
    const packagesDirectory = join(localAppData, "Microsoft", "WinGet", "Packages");
    if (existsSync(packagesDirectory)) {
      const packageDirectory = readdirSync(packagesDirectory)
        .find((name) => name.toLowerCase().startsWith("astral-sh.uv_"));
      if (packageDirectory) {
        const installedUv = join(packagesDirectory, packageDirectory, command);
        if (existsSync(installedUv)) return installedUv;
      }
    }
  }

  return command;
}

const child = spawn(
  findUv(),
  ["run", "--directory", "backend", "uvicorn", "app.main:app", "--reload"],
  { stdio: "inherit", shell: false },
);

child.on("error", (error) => {
  console.error("Could not start uv. Install uv or add it to PATH.", error.message);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  process.exit(code ?? 1);
});