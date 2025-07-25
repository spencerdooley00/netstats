#!/bin/bash

# Default metadata
AUTHOR="Spencer Dooley"
DATE=$(date +%F)  # ISO format, e.g., 2025-07-25

for file in articles/*.docx; do
    # Strip folder and extension
    base=$(basename "$file" .docx)
    slug="${base// /-}"  # replace spaces with hyphens for slugs
    output="articles/${base}.md"
    
    # Temp file for raw pandoc output
    tmp_output="articles/tmp_${base}.md"

    # Run pandoc conversion
    pandoc "$file" -f docx -t markdown -o "$tmp_output"

    # Extract first line of Markdown to use as title fallback
    title_line=$(head -n 1 "$tmp_output")
    title="${title_line//\#/}"        # remove '#' if it's a heading
    title="$(echo "$title" | xargs)"  # trim whitespace

    # Write frontmatter
    {
        echo "---"
        echo "title: \"$title\""
        echo "date: \"$DATE\""
        echo "author: \"$AUTHOR\""
        echo "description: \"\""
        echo "slug: \"$slug\""
        echo "image_url: \"/static/article_thumbs/netstats-preview-final.jpg\""
        echo "---"
        echo ""
        cat "$tmp_output"
    } > "$output"

    # Cleanup temp
    rm "$tmp_output"

    echo "✓ Created $output"
done
