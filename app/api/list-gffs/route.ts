import { readdir } from "node:fs/promises";
import { join } from "node:path";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    const gffsDir = join(process.cwd(), "public", "gffs");

    // Read all folders in public/gffs
    const folders = await readdir(gffsDir, { withFileTypes: true });

    const files: Array<{ value: string; label: string; group: string }> = [];

    // For each folder, find GFF files
    for (const folder of folders) {
      if (folder.isDirectory()) {
        const folderPath = join(gffsDir, folder.name);
        const folderFiles = await readdir(folderPath);

        // Filter for GFF files
        const gffFiles = folderFiles.filter(
          (file) => file.endsWith(".gff") || file.endsWith(".gff3"),
        );

        // Add each GFF file to the options
        for (const gffFile of gffFiles) {
          files.push({
            value: `/gffs/${folder.name}/${gffFile}`,
            label: gffFile,
            group: folder.name,
          });
        }
      }
    }

    return NextResponse.json({ files });
  } catch (error) {
    console.error("Error listing GFF files:", error);
    return NextResponse.json(
      { error: "Failed to list GFF files" },
      { status: 500 },
    );
  }
}
