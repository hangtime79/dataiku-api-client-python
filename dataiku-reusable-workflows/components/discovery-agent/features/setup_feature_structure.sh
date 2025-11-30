#!/bin/bash
# Base directory for features
BASE_DIR="."

echo "📂 Creating feature directory structure..."

# Create Phase directories (0 through 12)
for i in {0..12}; do
    PHASE_DIR="$BASE_DIR/phase-$i"
    mkdir -p "$PHASE_DIR"
    echo "  ✅ Created $PHASE_DIR"
done

# Create a README
cat << 'EOF' > "$BASE_DIR/README.md"
# Discovery Agent Features

This directory contains the atomic feature specifications for the Discovery Agent Enhancement Plan.

## Structure
- **phase-0/**: Foundation (Data Models)
- **phase-1/**: Dataset Metadata Extraction
- **phase-2/**: Recipe Metadata Extraction
- **phase-3/**: Libraries & Notebooks
- **phase-4/**: Flow Graph Extraction
- **phase-5/**: Wiki Quick Summary
- **phase-6/**: Wiki Navigation Menu
- **phase-7/**: Components Section
- **phase-8/**: Flow Diagram
- **phase-9/**: Technical Details
- **phase-10/**: Enhanced I/O
- **phase-11/**: Integration Testing
- **phase-12/**: Documentation
EOF