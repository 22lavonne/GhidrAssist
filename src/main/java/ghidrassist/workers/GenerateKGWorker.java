package ghidrassist.workers;

import ghidra.app.script.GhidraScript;
import ghidra.app.script.GhidraScriptProvider;
import ghidra.app.script.GhidraScriptUtil;
import ghidra.app.script.GhidraState;
import ghidra.program.model.listing.Program;
import ghidra.util.task.TaskMonitor;
import generic.jar.ResourceFile;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;

public class GenerateKGWorker extends AnalysisWorker<GenerateKGWorker.Result> {

    private final Program program;

    public static class Result {
        public final String outputPath;
        public Result(String outputPath) { this.outputPath = outputPath; }
    }

    public GenerateKGWorker(Program program) {
        this.program = program;
    }

    @Override
    protected Result doInBackground() throws Exception {
        Path workDir = Files.createTempDirectory("kg_build_");

        publishProgress(10, 100, "Extracting data from binary...");
        runExtractionScript(workDir);
        if (isCancelRequested()) return null;

        publishProgress(60, 100, "Materializing knowledge graph...");
        Path kgOutput = runMaterializationScript(workDir);

        publishProgress(100, 100, "Done.");
        return new Result(kgOutput.toString());
    }

    /**
     * Runs your existing PyGhidra extraction script in-process, the same way
     * Script Manager would (double-click), so it sees the already-open
     * `program` directly. No subprocess, no re-analysis.
     *
     * NOTE: replace "extract_kg_data.py" with your actual script's filename.
     * It must be discoverable on one of Script Manager's configured script
     * directories, or findScriptByName() will return null.
     */
    private void runExtractionScript(Path workDir) throws Exception {
        ResourceFile scriptFile = GhidraScriptUtil.findScriptByName("knowledge_node_extraction.py");
        if (scriptFile == null) {
            throw new RuntimeException(
                "Script not found: extract_kg_data.py — check it's on a directory " +
                "configured in Script Manager's script paths.");
        }

        GhidraScriptProvider provider = GhidraScriptUtil.getProvider(scriptFile);
        PrintWriter writer = new PrintWriter(System.out);
        GhidraScript script = provider.getScriptInstance(scriptFile, writer);

        // Hand the script the temp dir to write its intermediate output into.
        // Your script should read this via System.getProperty("kg.output.dir")
        // instead of hardcoding a path or prompting interactively (askFile/askDirectory
        // will hang waiting for a GUI dialog when run this way).
        System.setProperty("kg.output.dir", workDir.toString());

        // Passing null for tool/project — if your script calls getState().getTool()
        // or does project-folder operations, swap these for the real PluginTool/Project
        // (available from SemanticGraphController's `plugin` reference).
        GhidraState state = new GhidraState(null, null, program, null, null, null);
        script.execute(state, TaskMonitor.DUMMY, writer);
    }

    /**
     * Runs your standalone materialization script as an external process.
     * This one doesn't need Ghidra context — it just reads the extraction
     * output and builds/writes the KG.
     *
     * NOTE: replace the python path/script path with your actual setup.
     */
    private Path runMaterializationScript(Path workDir) throws Exception {
        Path output = workDir.resolve("kg_output");
        ProcessBuilder pb = new ProcessBuilder(
            "python3", "/ghidra_scripts/knowledge_node_materialization.py"
//            "--input", workDir.resolve("extracted.json").toString(),
//            "--output", output.toString()
        );
        pb.redirectErrorStream(true);
        Process proc = pb.start();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (isCancelRequested()) {
                    proc.destroyForcibly();
                    throw new InterruptedException("Cancelled");
                }
                publishProgress(-1, 100, line); // stream script stdout as status text
            }
        }

        int exitCode = proc.waitFor();
        if (exitCode != 0) {
            throw new RuntimeException("Materialization script exited with code " + exitCode);
        }
        return output;
    }
}