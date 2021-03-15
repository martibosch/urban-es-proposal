.PHONY: create_environment register_ipykernel agglom_lulc reclassify \
	candidate_pixels vulnerable_pop heat_mitigation one_pager_docx \
	one_pager_pdf roadmap_docx roadmap_pdf

#################################################################################
# GLOBALS                                                                       #
#################################################################################

## variables
PROJECT_NAME = urban-es-proposal

DATA_DIR = data
DATA_RAW_DIR := $(DATA_DIR)/raw
DATA_INTERIM_DIR := $(DATA_DIR)/interim
DATA_PROCESSED_DIR := $(DATA_DIR)/processed

CODE_DIR = urban_es_proposal

NOTEBOOKS_DIR = notebooks

REPORTS_DIR = reports

## rules
define MAKE_DATA_SUB_DIR
$(DATA_SUB_DIR): | $(DATA_DIR)
	mkdir $$@
endef
$(DATA_DIR):
	mkdir $@
$(foreach DATA_SUB_DIR, \
	$(DATA_RAW_DIR) $(DATA_INTERIM_DIR) $(DATA_PROCESSED_DIR), \
	$(eval $(MAKE_DATA_SUB_DIR)))

## Set up python interpreter environment
create_environment:
	conda env create -f environment.yml

## Register the environment as an IPython kernel for Jupyter
register_ipykernel:
	python -m ipykernel install --user --name $(PROJECT_NAME) \
		--display-name "Python ($(PROJECT_NAME))"


#################################################################################
# COMMANDS                                                                      #
#################################################################################

# Download the cadastre and desired extent shapefile, then crop the cadastre to
# such an extent rasterize it
## variables
AGGLOM_EXTENT_DIR := $(DATA_RAW_DIR)/agglom-extent
AGGLOM_EXTENT_ZENODO_URI = \
	https://zenodo.org/record/4311544/files/agglom-extent.zip?download=1
AGGLOM_EXTENT_SHP := $(AGGLOM_EXTENT_DIR)/agglom-extent.shp
CADASTRE_FILE_KEY = cantons/vaud/cadastre/Cadastre_agglomeration.zip
CADASTRE_UNZIP_FILEPATTERN = \
	Cadastre/(NPCS|MOVD)_CAD_TPR_(BATHS|CSBOIS|CSDIV|CSDUR|CSEAU|CSVERT)_S.*
CADASTRE_DIR := $(DATA_RAW_DIR)/cadastre
CADASTRE_SHP := $(CADASTRE_DIR)/cadastre.shp
CADASTRE_TIF := $(DATA_INTERIM_DIR)/cadastre.tif
AGGLOM_LULC_TIF := $(DATA_INTERIM_DIR)/agglom-lulc.tif
#### do not delete `CADASTRE_SHP` despite chained rule
.PRECIOUS: $(CADASTRE_SHP)
### code
DOWNLOAD_S3_PY := $(CODE_DIR)/download_s3.py
MAKE_CADASTRE_SHP_FROM_ZIP_PY := $(CODE_DIR)/make_cadastre_shp_from_zip.py
MAKE_AGGLOM_LULC_PY := $(CODE_DIR)/make_agglom_lulc.py

## rules
$(AGGLOM_EXTENT_DIR): | $(DATA_RAW_DIR)
	mkdir $@
$(CADASTRE_DIR): | $(DATA_RAW_DIR)
	mkdir $@
$(CADASTRE_DIR)/%.zip: | $(CADASTRE_DIR)
	python $(DOWNLOAD_S3_PY) $(CADASTRE_FILE_KEY) $@
$(CADASTRE_DIR)/%.shp: $(CADASTRE_DIR)/%.zip $(MAKE_CADASTRE_SHP_FROM_ZIP_PY)
	python $(MAKE_CADASTRE_SHP_FROM_ZIP_PY) $< $@ \
		"$(CADASTRE_UNZIP_FILEPATTERN)"
	touch $@
$(AGGLOM_LULC): $(CADASTRE_SHP) $(AGGLOM_EXTENT_SHP) $(MAKE_AGGLOM_LULC_PY) \
	| $(DATA_INTERIM_DIR)
	python $(MAKE_AGGLOM_LULC_PY) $(CADASTRE_SHP) $(AGGLOM_EXTENT_SHP)
agglom_lulc: $(AGGLOM_LULC_TIF)

# Reclassify
## variables
TREE_CANOPY_ZENODO_URI = \
	https://zenodo.org/record/4310112/files/tree-canopy.tif?download=1
TREE_CANOPY_TIF := $(DATA_RAW_DIR)/tree-canopy.tif
BLDG_COVER_TIF := $(DATA_RAW_DIR)/bldg-cover.tif
TREE_COVER_TIF := $(DATA_INTERIM_DIR)/tree-cover.tif
BIOPHYSICAL_TABLE_ZENODO_URI = \
	https://zenodo.org/record/4316572/files/biophysical-table.csv?download=1
BIOPHYSICAL_TABLE_CSV := $(DATA_RAW_DIR)/biophysical-table.csv
RECLASSIF_TABLE_CSV := $(DATA_PROCESSED_DIR)/biophysical-table.csv
RECLASSIF_LULC_TIF := $(DATA_PROCESSED_DIR)/agglom-lulc.tif
### code
MAKE_BLDG_COVER_PY := $(CODE_DIR)/make_bldg_cover.py

## rules
$(TREE_CANOPY_TIF): | $(DATA_RAW_DIR)
	wget $(TREE_CANOPY_ZENODO_URI) -O $@
$(TREE_COVER_TIF): $(AGGLOM_LULC_TIF) $(TREE_CANOPY_TIF) | $(DATA_INTERIM_DIR)
	swiss-uhi-utils compute-feature-cover $(AGGLOM_LULC_TIF) \
		$(TREE_CANOPY_TIF) $@
$(BLDG_COVER_TIF): $(AGGLOM_LULC_TIF) $(CADASTRE_SHP) $(MAKE_BLDG_COVER_PY) \
	| $(DATA_RECLASSIF_DIR)
	python $(MAKE_BLDG_COVER_PY) $(AGGLOM_LULC_TIF) $(CADASTRE_SHP) $@
$(BIOPHYSICAL_TABLE_CSV): | $(DATA_RAW_DIR)
	wget $(BIOPHYSICAL_TABLE_ZENODO_URI) -O $@
$(RECLASSIF_LULC_TIF) $(RECLASSIF_TABLE_CSV): $(AGGLOM_LULC_TIF) \
	$(TREE_COVER_TIF) $(BLDG_COVER_TIF) $(BIOPHYSICAL_TABLE_CSV) \
	$(MAKE_RECLASSIFY_PY) | $(DATA_PROCESSED_DIR)
	swiss-uhi-utils reclassify $(AGGLOM_LULC_TIF) $(TREE_COVER_TIF) \
		$(BLDG_COVER_TIF) $(BIOPHYSICAL_TABLE_CSV) \
		$(RECLASSIF_LULC_TIF) $(RECLASSIF_TABLE_CSV)
### Rule with multiple targets https://bit.ly/35B8YdU
$(RECLASSIF_TABLE_CSV): $(RECLASSIF_LULC_TIF)
reclassify: $(RECLASSIF_LULC_TIF) $(RECLASSIF_TABLE_CSV)


# Candidate pixels
## variables
CANDIDATE_PIXELS_TIF := $(DATA_PROCESSED_DIR)/candidate-pixels.tif
### code
MAKE_CANDIDATE_PIXELS_PY := $(CODE_DIR)/make_candidate_pixels.py

## rules
$(CANDIDATE_PIXELS_TIF): $(RECLASSIF_LULC_TIF) $(RECLASSIF_TABLE_CSV) \
	$(MAKE_CANDIDATE_PIXELS_PY)
	python $(MAKE_CANDIDATE_PIXELS_PY) $(RECLASSIF_LULC_TIF) \
		$(RECLASSIF_TABLE_CSV) $@
candidate_pixels: $(CANDIDATE_PIXELS_TIF)


# Statpop
## variables
STATPOP_URI = https://www.bfs.admin.ch/bfsstatic/dam/assets/14027479/master
STATPOP_DIR := $(DATA_RAW_DIR)/statpop
STATPOP_CSV := $(STATPOP_DIR)/statpop-2019.csv
AGGLOM_EXTENT_ZENODO_URI = \
	https://zenodo.org/record/4311544/files/agglom-extent.zip?download=1
AGGLOM_EXTENT_SHP := $(AGGLOM_EXTENT_DIR)/agglom-extent.shp
VULNERABLE_POP_TIF := $(DATA_PROCESSED_DIR)/vulnerable-pop.tif
### code
MAKE_VULNERABLE_POP_PY := $(CODE_DIR)/make_vulnerable_pop.py

## rules
$(STATPOP_DIR): | $(DATA_RAW_DIR)
	mkdir $@
$(STATPOP_DIR)/%.zip: | $(STATPOP_DIR)
	wget $(STATPOP_URI) -O $@
$(STATPOP_DIR)/%.csv: $(STATPOP_DIR)/%.zip
	unzip -j $< 'STATPOP2019.csv' -d $(STATPOP_DIR)
	mv $(STATPOP_DIR)/STATPOP2019.csv $(STATPOP_CSV)
	touch $@
$(VULNERABLE_POP_TIF): $(STATPOP_CSV) $(AGGLOM_EXTENT_SHP) \
	$(CANDIDATE_PIXELS_TIF) $(MAKE_VULNERABLE_POP_PY)
	python $(MAKE_VULNERABLE_POP_PY) $(STATPOP_CSV) $(AGGLOM_EXTENT_SHP) \
		$(CANDIDATE_PIXELS_TIF) $@
vulnerable_pop: $(VULNERABLE_POP_TIF)

# Heat mitigation
HEAT_MITIGATION_URI = https://github.com/charlottegiseleweil/ES-lausanne/raw/gh-pages/static/media/heat-mitigation-0.5-4326.49a82243.tif
HEAT_MITIGATION_TIF := $(DATA_RAW_DIR)/heat-mitigation.tif
$(HEAT_MITIGATION_TIF): | $(DATA_RAW_DIR)
	wget $(HEAT_MITIGATION_URI) -O $@
heat_mitigation: $(HEAT_MITIGATION_TIF)


# One pager
## variables
ONE_PAGER_TEMPLATE_URI = https://raw.githubusercontent.com/Wandmalfarbe/pandoc-latex-template/v2.0.0/eisvogel.tex
ONE_PAGER_TEMPLATE_TEX := $(REPORTS_DIR)/eisvogel.tex
ONE_PAGER_MD := $(REPORTS_DIR)/one-pager.md
ONE_PAGER_DOCX := $(REPORTS_DIR)/one-pager.docx
ONE_PAGER_PDF := $(REPORTS_DIR)/one-pager.pdf

## rules
$(ONE_PAGER_TEMPLATE_TEX): | $(REPORTS_DIR)
	wget $(ONE_PAGER_TEMPLATE_URI) -O $@
define MAKE_ONE_PAGER
$(ONE_PAGER_EXT):  $(ONE_PAGER_MD) | $(ONE_PAGER_TEMPLATE_TEX)
	pandoc $$< -o $$@ -f markdown --template $(ONE_PAGER_TEMPLATE_TEX)
endef
$(foreach ONE_PAGER_EXT, $(ONE_PAGER_DOCX) $(ONE_PAGER_PDF), \
	$(eval $(MAKE_ONE_PAGER)))
one_pager_docx: $(ONE_PAGER_DOCX)
one_pager_pdf: $(ONE_PAGER_PDF)

# Roadmap
## variables
ROADMAP_MD := $(REPORTS_DIR)/roadmap.md
ROADMAP_DOCX := $(REPORTS_DIR)/roadmap.docx
ROADMAP_PDF := $(REPORTS_DIR)/roadmap.pdf

## rules
define MAKE_ROADMAP
$(ROADMAP_EXT):  $(ROADMAP_MD) | $(REPORTS_DIR)
	pandoc $$< -o $$@ -f markdown
endef
$(foreach ROADMAP_EXT, $(ROADMAP_DOCX) $(ROADMAP_PDF), $(eval $(MAKE_ROADMAP)))
roadmap_docx: $(ROADMAP_DOCX)
roadmap_pdf: $(ROADMAP_PDF)

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := show-help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: show-help
show-help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) == Darwin && echo '--no-init --raw-control-chars')
