package ghidrassist.workers;

import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionManager;
import ghidra.program.model.listing.Program;

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
        publishProgress(10, 100, "Starting KG generation (stub)...");

        // Bare-minimum placeholder: just prove we can touch the Program API
        // and write a file. Replace this block with your real scripts later.
        FunctionManager fm = program.getFunctionManager();
        int count = 0;
        for (Function f : fm.getFunctions(true)) {
            if (isCancelRequested()) return null;
            count++;
        }

        publishProgress(70, 100, "Writing stub output...");
        Path workDir = Files.createTempDirectory("kg_build_");
        Path outputFile = workDir.resolve("kg_stub.txt");
        Files.writeString(outputFile, "Stub KG generation.\nFunction count: " + count + "\n");

        publishProgress(100, 100, "Done.");
        return new Result(outputFile.toString());
    }
}