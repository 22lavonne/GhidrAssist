package ghidrassist.workers;

import ghidra.app.script.GhidraScript;
import ghidra.app.script.GhidraScriptProvider;
import ghidra.app.script.GhidraScriptUtil;
import ghidra.app.script.GhidraState;
import ghidra.program.model.listing.Program;
import ghidra.util.task.TaskMonitor;
import generic.jar.ResourceFile;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class GenerateKGWorker extends AnalysisWorker<GenerateKGWorker.Result> {

    private final Program program;
    private final String runDirName;

    public static class Result {
        public final String outputPath;
        public Result(String outputPath) { this.outputPath = outputPath; }
    }

    /**
     * @param program    the currently open program
     * @param runDirName the output directory name, chosen by the user via a
     *                    dialog in SemanticGraphController.handleGenerateKG()
     *                    BEFORE this worker is constructed. This is what both
     *                    the extraction and materialization scripts write to
     *                    / read from — generated/prompted once, here, in Java,
     *                    rather than inside either script.
     */
    public GenerateKGWorker(Program program, String runDirName) {
        this.program = program;
        this.runDirName = runDirName;
    }

    @Override
    protected Result doInBackground() throws Exception {
        ResourceFile scriptFile = GhidraScriptUtil.findScriptByName("combined_extraction.py");
        if (scriptFile == null) {
            throw new RuntimeException(
                "Extraction script not found: extract_kg_data.py — check it's on a " +
                "directory configured in Script Manager's script paths.");
        }
        // Parent of the extraction script == your ghidra_scripts directory, where
        // knowledge_node_materialization.py also lives.
        Path scriptsDir = scriptFile.getParentFile().getFile(false).toPath();

        publishProgress(10, 100, "Extracting data from binary...");
        runExtractionScript(scriptFile, runDirName);
        if (isCancelRequested()) return null;

        publishProgress(60, 100, "Materializing knowledge graph...");
        Path kgOutput = runMaterializationScript(scriptsDir, runDirName);

        publishProgress(100, 100, "Done.");
        return new Result(kgOutput.toString());
    }

    /**
     * Runs your existing PyGhidra extraction script in-process, the same way
     * Script Manager would (double-click), so it sees the already-open
     * `program` directly. No subprocess, no re-analysis.
     *
     * Hands the script its output directory name by writing a small handoff
     * file (.kg_output_dir) next to the script, which the script reads instead
     * of prompting. This is used rather than stdin (input() has no real console
     * when a script is launched this way, and swapping System.in is unsafe
     * besides, since Ghidra's own PyGhidra console shares this JVM's System.in)
     * and rather than a JVM system property (which would require the script to
     * import java.lang.System through the JPype bridge — valid at runtime under
     * PyGhidra, but it breaks editors, linting, and standalone runs).
     *
     * The file is always deleted afterwards, so running the script manually
     * from Script Manager still falls back to its askString() prompt.
     */
    private void runExtractionScript(ResourceFile scriptFile, String runDirName) throws Exception {
        GhidraScriptProvider provider = GhidraScriptUtil.getProvider(scriptFile);
        PrintWriter writer = new PrintWriter(System.out);
        GhidraScript script = provider.getScriptInstance(scriptFile, writer);

        Path scriptsDir = scriptFile.getParentFile().getFile(false).toPath();
        Path handoff = scriptsDir.resolve(".kg_output_dir");
        Files.write(handoff, runDirName.getBytes(StandardCharsets.UTF_8));

        try {
            // Passing null for tool/project — if your script calls getState().getTool()
            // or does project-folder operations, swap these for the real PluginTool/
            // Project (available from SemanticGraphController's `plugin` reference).
            GhidraState state = new GhidraState(null, null, program, null, null, null);
            script.execute(state, TaskMonitor.DUMMY, writer);
        } finally {
            writer.flush();
            // Always clean up, even if the script threw, so a stale handoff file
            // can never silently hijack a later manual run of the script.
            try {
                Files.deleteIfExists(handoff);
            } catch (IOException ignored) {
                // Non-fatal: worst case the next manual run reuses this name.
            }
        }

        // Verify extraction actually produced its outputs before moving on —
        // script.execute() can return normally even if the script errored
        // internally (Ghidra logs script exceptions to its own Console rather
        // than propagating them here), so check for real instead of assuming.
        Path outDir = scriptsDir.resolve(runDirName);
        String[] required = { "binaries.json", "function-node.json", "externals.json", "modules.json", "class.json", "dll.json", "function.json", "instruction.json", "label.json", "local_variable.json", "namespace.json", "parameter.json" };
        for (String name : required) {
            if (!Files.exists(outDir.resolve(name))) {
                throw new RuntimeException(
                    "Extraction did not produce " + name + " in " + outDir +
                    " — check Ghidra's Console window for a Python traceback from the extraction script.");
            }
        }
    }

    /**
     * Runs your standalone materialization script as a genuinely separate OS
     * process, so feeding it stdin here is safe (it does NOT touch Ghidra's
     * own console/System.in) — no script changes needed for this stage.
     *
     * Working directory is set to your ghidra_scripts folder so the script's
     * own `Path(__file__).resolve().parent / dir_name` resolves the same way
     * it does when you run it manually.
     *
     * Still requires symbol-output.ttl to already exist in runDirName (from
     * your separate symbol materialization script) — that's a known next step,
     * not something this method currently does.
     */
    private Path runMaterializationScript(Path scriptsDir, String runDirName) throws Exception {
        publishProgress(-1, 100, "Running in: " + scriptsDir);

        Process proc = startMaterialization(scriptsDir, runDirName);

        // The directory name is passed as a command-line argument now, so there
        // is nothing to write. Close stdin so the script can never block waiting
        // on input() if it somehow falls through to the interactive prompt.
        proc.getOutputStream().close();

        // Buffer everything the script prints. stderr is merged into stdout by
        // redirectErrorStream(true), so a Python traceback lands here too — it
        // must be retained, otherwise a failure gives us nothing but a bare
        // exit code to debug from.
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(proc.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (isCancelRequested()) {
                    proc.destroyForcibly();
                    throw new InterruptedException("Cancelled");
                }
                output.append(line).append(System.lineSeparator());
                publishProgress(-1, 100, line);
            }
        }

        int exitCode = proc.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException(
                "Materialization script exited with code " + exitCode +
                ". Script output:" + System.lineSeparator() +
                (output.length() == 0 ? "(no output)" : output.toString()));
        }

        Path result = scriptsDir.resolve(runDirName).resolve("combined-output.ttl");
        // The script calls a bare sys.exit() on some failure paths, which exits
        // with status 0 — so a zero exit code alone doesn't prove it wrote anything.
        if (!Files.exists(result)) {
            throw new RuntimeException(
                "Materialization reported success but " + result + " does not exist. " +
                "Script output:" + System.lineSeparator() +
                (output.length() == 0 ? "(no output)" : output.toString()));
        }
        return result;
    }

    /**
     * Runs the materialization script inside WSL, using WSL's own python3 — the
     * environment where rdflib and everything else this script needs are already
     * installed, matching how it's been run manually up to now.
     *
     * Launching straight into WSL rather than a Windows-side python3 also sidesteps
     * the "SRE module mismatch" failure from before: that came from the JVM's
     * PYTHONHOME/PYTHONPATH (set by PyGhidra's own embedded CPython) leaking into
     * a Windows python3 subprocess. wsl.exe does not forward arbitrary Windows
     * environment variables into the guest shell unless they're explicitly listed
     * in WSLENV, so that particular contamination shouldn't recur here — PYTHONHOME/
     * PYTHONPATH are stripped from wsl.exe's own environment anyway as a safety net.
     *
     * The script itself is invoked by its WSL-side path (translated below), and
     * takes its output directory name as a plain argument — it no longer depends
     * on the process's working directory (see combined_materialization.py), which
     * matters because Windows can't reliably set a UNC path like \\wsl$\... as a
     * working directory in the first place.
     *
     * Set WSL_DISTRO if you have more than one distro installed and need a specific
     * one; leave it null to use whichever wsl.exe picks by default. If you'd rather
     * skip WSL entirely and use a Windows interpreter (with rdflib etc. installed
     * there instead), set PYTHON_OVERRIDE to its absolute path and WSL is bypassed.
     */
    private static final String WSL_DISTRO = null; // e.g. "Ubuntu"
    private static final String PYTHON_OVERRIDE = null; // e.g. "C:\\Python311\\python.exe"

    private Process startMaterialization(Path scriptsDir, String runDirName) throws Exception {
        Path scriptPath = scriptsDir.resolve("combined_materialization.py");
        if (!Files.exists(scriptPath)) {
            throw new RuntimeException("Materialization script not found at " + scriptPath);
        }

        if (PYTHON_OVERRIDE != null) {
            return startWithWindowsInterpreter(PYTHON_OVERRIDE, scriptPath, scriptsDir, runDirName);
        }
        return startInWsl(scriptPath, runDirName);
    }

    private Process startWithWindowsInterpreter(
            String exe, Path scriptPath, Path scriptsDir, String runDirName) throws Exception {
        // -E ignores PYTHON* environment variables, -u makes output unbuffered so
        // progress lines arrive as the script runs rather than all at once.
        ProcessBuilder pb = new ProcessBuilder(exe, "-E", "-u", scriptPath.toString(), runDirName);
        pb.directory(scriptsDir.toFile());
        pb.redirectErrorStream(true);
        pb.environment().remove("PYTHONHOME");
        pb.environment().remove("PYTHONPATH");
        pb.environment().remove("PYTHONSTARTUP");
        pb.environment().put("PYTHONIOENCODING", "utf-8");

        Process proc = pb.start();
        publishProgress(-1, 100, "Using interpreter: " + exe);
        return proc;
    }

    private Process startInWsl(Path scriptPath, String runDirName) throws Exception {
        WslLocation loc = resolveWslLocation(scriptPath);
        // An explicit WSL_DISTRO always wins; otherwise use whatever distro the
        // \\wsl$\<Distro>\... path itself named — NOT wsl.exe's system default,
        // which may be a different distro than the one the files actually live in
        // and would otherwise fail with a "no such file" that looks like a bad
        // path translation when it's really just the wrong filesystem.
        String distro = (WSL_DISTRO != null) ? WSL_DISTRO : loc.distro;

        List<String> cmd = new ArrayList<>();
        cmd.add("wsl.exe");
        if (distro != null) {
            cmd.add("-d");
            cmd.add(distro);
        }
        cmd.add("--");
        cmd.add("python3");
        cmd.add("-u");
        cmd.add(loc.path);
        cmd.add(runDirName);

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        pb.environment().remove("PYTHONHOME");
        pb.environment().remove("PYTHONPATH");

        try {
            Process proc = pb.start();
            publishProgress(-1, 100,
                "Using WSL distro '" + distro + "', python3 on: " + loc.path);
            return proc;
        } catch (IOException e) {
            throw new RuntimeException(
                "Could not launch wsl.exe. Make sure WSL is installed and on PATH, " +
                "or set PYTHON_OVERRIDE in GenerateKGWorker to run a Windows " +
                "interpreter instead.", e);
        }
    }

    /** Windows->WSL path translation result: the distro it belongs to (if known) and the translated path. */
    private static final class WslLocation {
        final String distro; // null if not determinable (e.g. a genuine C:\ path)
        final String path;
        WslLocation(String distro, String path) {
            this.distro = distro;
            this.path = path;
        }
    }

    /**
     * Converts a Windows path to the equivalent path inside WSL, and identifies
     * which distro it belongs to when that's derivable from the path itself.
     *
     * Paths under \\wsl$\<Distro>\... or \\wsl.localhost\<Distro>\... are already
     * WSL's own filesystem, exposed to Windows via a network redirector — which is
     * what we have here, since the scripts live in the WSL filesystem. The UNC/
     * distro prefix is stripped directly rather than asking `wslpath` to do the
     * translation: in testing, `wslpath -a` did not handle this UNC form correctly
     * and silently produced a wrong, unrelated path (it's built primarily for
     * translating C:\ drive-letter paths, not these UNC forms). Critically, this
     * also recovers the *actual* distro name from the path — running via wsl.exe's
     * default distro instead would silently target the wrong filesystem if more
     * than one distro is installed.
     *
     * A genuine C:\ path (e.g. if the scripts ever move onto the Windows-native
     * filesystem) is still translated via `wslpath`, since \\wsl$\ stripping does
     * not apply there and wslpath handles plain drive letters correctly; in that
     * case there's no distro to recover from the path, so WSL_DISTRO (or wsl.exe's
     * default) is used instead.
     */
    private WslLocation resolveWslLocation(Path windowsPath) throws Exception {
        String s = windowsPath.toString();

        String rest = stripUncPrefixIgnoreCase(s, "\\\\wsl$\\");
        if (rest == null) {
            rest = stripUncPrefixIgnoreCase(s, "\\\\wsl.localhost\\");
        }
        if (rest != null) {
            // rest is now "<Distro>\home\emiller\...\combined_materialization.py".
            int sep = rest.indexOf('\\');
            String distro = (sep >= 0) ? rest.substring(0, sep) : rest;
            String tail = (sep >= 0) ? rest.substring(sep + 1) : "";
            return new WslLocation(distro, "/" + tail.replace('\\', '/'));
        }

        return new WslLocation(null, wslpathViaCli(s));
    }

    private static String stripUncPrefixIgnoreCase(String path, String prefix) {
        if (path.length() >= prefix.length()
                && path.substring(0, prefix.length()).equalsIgnoreCase(prefix)) {
            return path.substring(prefix.length());
        }
        return null;
    }

    private String wslpathViaCli(String windowsPath) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add("wsl.exe");
        if (WSL_DISTRO != null) {
            cmd.add("-d");
            cmd.add(WSL_DISTRO);
        }
        cmd.add("--");
        cmd.add("wslpath");
        cmd.add("-a");
        cmd.add(windowsPath);

        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        Process proc = pb.start();

        String output;
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(proc.getInputStream(), StandardCharsets.UTF_8))) {
            output = reader.readLine();
        }

        int exitCode = proc.waitFor();
        if (exitCode != 0 || output == null || output.isBlank()) {
            throw new RuntimeException(
                "Could not translate path to WSL via wslpath: " + windowsPath +
                " (exit " + exitCode + ", output: " + output + ")");
        }
        return output.trim();
    }
}