/**
 * Generate above-the-fold CSS directly from the existing LESS sources.
 *
 * The full CodeStitch section files remain the single styling source. Each
 * critical file stops at the first below-the-fold section marker, is compiled
 * by LESS, and is loaded before the corresponding deferred full stylesheet.
 */
const fs = require("node:fs/promises");
const path = require("node:path");
const less = require("less");

const projectRoot = path.resolve(__dirname, "..");

const criticalFiles = [
    {
        source: "src/assets/less/critical.less",
        output: "src/assets/css/home-critical.css",
        nextSection: "Services",
    },
    {
        source: "src/assets/less/about.less",
        output: "src/assets/css/about-critical.css",
        nextSection: "Side By Side",
    },
    {
        source: "src/assets/less/services.less",
        output: "src/assets/css/services-critical.css",
        nextSection: "Services",
    },
    {
        source: "src/assets/less/contact.less",
        output: "src/assets/css/contact-critical.css",
        nextSection: "Contact",
    },
];

async function buildCriticalFile({ source, output, nextSection }) {
    const sourcePath = path.join(projectRoot, source);
    const outputPath = path.join(projectRoot, output);
    const lessSource = await fs.readFile(sourcePath, "utf8");
    const sectionMatch = new RegExp(`^<---\\s+${nextSection}\\s+-->`, "m").exec(lessSource);

    if (!sectionMatch) {
        throw new Error(`Could not find the next-section marker in ${source}`);
    }

    const sectionComment = lessSource.lastIndexOf("/*--", sectionMatch.index);
    const criticalLess = lessSource.slice(0, sectionComment);
    const compiled = await less.render(criticalLess, {
        compress: true,
        filename: sourcePath,
    });

    await fs.writeFile(outputPath, `${compiled.css}\n`, "utf8");
    return `${output} (${Buffer.byteLength(compiled.css)} bytes)`;
}

Promise.all(criticalFiles.map(buildCriticalFile))
    .then((files) => console.log(`Generated critical CSS:\n${files.join("\n")}`))
    .catch((error) => {
        console.error(error);
        process.exitCode = 1;
    });
