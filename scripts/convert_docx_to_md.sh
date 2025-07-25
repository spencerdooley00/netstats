#!/bin/bash

# Loop over all .docx files in the articles folder
for file in articles/*.docx; do
    # Get the base filename without extension
    base_name=$(basename "$file" .docx)
    
    # Define output path
    output="articles/${base_name}.md"

    # Convert with pandoc
    pandoc "$file" -f docx -t markdown -o "$output"
    
    echo "Converted $file → $output"
done