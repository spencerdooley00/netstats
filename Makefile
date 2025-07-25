# Convert all .docx articles to .md
convert:
	./scripts/convert_docx_to_md.sh

# Deploy via AWS Copilot (after converting)
deploy: convert
	copilot svc deploy --name frontend --env prod

# Just run the app locally (optional)
run:
	python3 application.py