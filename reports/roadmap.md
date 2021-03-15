# Roadmap

## 1. Fine-scale evaluation of the UHI simulation

* Use the last chapter of the thesis for a literature review
* Use high-resolution temperature rasters based on Zumwald et al. [1]
* Improve the [swiss-uhi-utils](https://github.com/martibosch/swiss-uhi-utils) package with a module to create local climate zone (LCZ) maps from open data (Swiss Cadastre, OpenStreetMap, SWISSIMAGE...). To avoid "re-inventing the wheel", consider first [the approach used in the WUADAPT project](http://www.wudapt.org/lcz/lcz-framework/).
* Compare several models, e.g., the InVEST urban cooling model, [TEB](https://github.com/TEB-model/teb), [UWG](https://github.com/ladybug-tools/uwg), [COSMO-BEP-Tree](https://github.com/gianlum/UCPgenerator)...
* Evaluate the diurnal UHI cycle and the model performance along it
* Select a UHI model based on the results
* **Output**: journal article (+code repository in GitHub)

## 2. Implement a reusable library to model the urban recreation service

* Based on the approaches of Grêt-Regamey et al. [2], Liu et al. [3] and the like
* **Ouptut**: Python library (installable with `pip` and `conda`) with documentation site and examples. Optionally, an article to [JOSS](https://joss.theoj.org).

## 3. Validate the InVEST urban flood regulation model

* Try to validate the model in a watershed in the Lausanne area
* Compare performance against, e.g., [wflow](https://github.com/openstreams/wflow/), [PySTREAM](https://github.com/martibosch/pystream), [Landlab (overland flow component)](https://github.com/landlab/landlab) and the like
* **Output**: journal article (+code repository in GitHub)

## 4. Longitudinal study of urban ecosystem serices in Switzerland

* Select agglomerations based on watershed criteria (e.g., ensure that we have MeteoSwiss data) so that we can evaluate the flood risk
* Considered ecosystem services: 
    * urban cooling (hopefully with an improved model result of the first task)
    * recreation (based on the output of the second task)
    * flood regulation (based on the output of the third task)
    * carbon sequestration (with the InVEST carbon model)
* Potentially move the MeteoSwiss module of the [swiss-uhi-utils](https://github.com/martibosch/swiss-uhi-utils) package to a dedicated package to deal with MeteoSwiss spatial climate analysis products
* **Output**: journal article (+code repository in GitHub)

## 5. Deploy a cloud-based platform to asses urban ecosystem services

* Create Intake plugins for the required data sources to ease the (automated) access, processing and management of the data
* Create a custom Renku environment (see [the dedicated Renku documentation](https://renku.readthedocs.io/en/0.7.7/user/interactive_customizing.html)) with all the required packages installed
* **Output**: cloud platform with a web interface


## Referneces

1. Zumwald, Marius, et al. "Mapping urban temperature using crowd-sensing data and machine learning." Urban Climate 35 (2021): 100739.
2. Grêt-Regamey, Adrienne, et al. "How urban densification influences ecosystem services—a comparison between a temperate and a tropical city." Environmental Research Letters 15.7 (2020): 075001.
3. Liu, Hongxiao, et al. "Supply and demand assessment of urban recreation service and its implication for greenspace planning-A case study on Guangzhou." Landscape and Urban Planning 203 (2020): 103898.

